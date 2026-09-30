# Memory

## Telegram vocab-bot reply latency — DONE (2026-09-27)

Live on an Oracle free-tier VPS at **92.4.74.1**. Runbook: `vocab-bot/deploy/ORACLE_VPS.md`.

- **Interactive replies** now come from the VPS: `telegram_listener.py` as a warm
  `getUpdates` long-poll (45s) under systemd (`vocab-listener.service`).
  GH Actions is now only the 6 AM / 6 PM scheduled jobs (via the CF `vocab-conductor` cron).
- **The CF worker webhook was deleted** (`deleteWebhook`) — the worker still holds the
  cron, so daily/evening are unaffected. Rollback = `cf-worker/setup_webhook.py`
  (needs `WORKER_URL` + `TELEGRAM_WEBHOOK_SECRET`).
- **Secrets** live at `/etc/vocab-bot.env` (`-rw------- root root`): bot token, admin
  chat id, group id `-1004431038044`, Gemini key. Not on any local disk.
- **VPS git auth** = deploy key `vocab-bot-vps-deploy` (id 164619969, write-enabled),
  private half only on the VPS. Local admin key is `~/.ssh/vocab_vps` (Windows) — never
  read it, only ever use `ssh -i`.
- **Keepalive:** cron `17 */6 * * *` runs `deploy/keepalive.sh` (45s CPU burn). Required —
  Oracle reclaims Always Free compute under ~20% utilisation, and a long-poll bot idles at
  ~0%. The box was already reclaimed once (stale `13.53.131.202` in known_hosts).

## Latency facts (measured on the VPS, don't re-derive)

- Telegram round-trip ≈ **0.41s** → ~0.5s replies is the practical floor.
- `set_bot_commands()` ≈ **2.14s** (4 API calls) — runs *after* replies, every cycle.
  Putting it first was the whole cost of a 3s reply.
- **Gemini key is a relay/proxy, not Google's API.** It takes 10-20s for *any* prompt — a
  trivial `"Say OK"` measured 17.96s. `gemini-2.5-flash` / `-lite` / `2.0-flash` all 404 on
  this key. Prompt/model/token tuning cannot improve it, so homework sends an instant ack
  and the full report follows. Don't waste time retrying this.
- `git fetch` ≈ 0.7s, so the loop syncs every 10th cycle, not every cycle.

## Gotchas that cost real time

- **The VPS pushes continuously.** Always `git fetch` + rebase before pushing locally, or
  the push is rejected non-fast-forward. This happens several times an hour.
- `git add` aborts the *whole* command if any pathspec is missing — that silently killed
  `push_state` for a whole session (see `tests/test_vps_listener.sh`).
- Windows checkout would store CRLF in the shell scripts and break them on the VPS;
  `.gitattributes` pins `*.sh` and `deploy/*.service` to LF.
- The listener log at `/var/log/vocab-listener.log` is timestamped; measure latency there.

## Multi-minute Telegram replies — root cause was a SECOND listener (fixed 2026-09-30)

A `/savedwords` sent right after a `/save` took ~3 min. It was not the handler
(`saved_words_handler` is pure file I/O; 0.6s from fetch to reply). Two causes stacked:

- **An orphaned root listener ran for ~49h.** Someone had started it by hand with
  `sudo -s bash /opt/vocab-bot/vps_listener.sh`; its SSH parent died and init reparented
  it, so it survived. It ran *alongside* the systemd one — two `getUpdates` pollers
  sharing one `update_offset.txt`, so they clobbered each other's offset. Find any second
  instance with `ps -eo user,pid,etimes,cmd | grep vps_listener`; there must be exactly
  **one** tree (MainPID + its pipeline subshell). Never start the listener by hand — the
  unit has `Restart=always` and is the only thing that should own it.
- **Root-owned git files broke the real service.** The orphan's `push_state` wrote
  `.git/index` and loose objects as root, so the `ubuntu` service's `git add`/`push`/
  `fetch` all failed (`insufficient permission for adding an object`, `failed to insert
  into database`, `unpack-objects failed`) — 85 hits in the log. The bot still replied,
  but the VPS silently stopped self-updating (stale code) and every state push failed.
  Fix: `sudo chown -R ubuntu:ubuntu /opt/vocab-bot`. **A `chown` alone is not enough** —
  it was undone within minutes until the root process was killed. Check with
  `sudo find /opt/vocab-bot -not -user ubuntu` (must be empty).
- **Why a failed push cost ~100s of dead air.** `push_state` runs *after* `getUpdates`
  returns, so it is pure dead time in front of the next poll. Its retry loop slept
  5+10+15+20+25 = 75s plus 5 pushes and 5 pulls — measured 102s between the `/save`
  reply (09:29:32) and the poll that took `/savedwords` (09:31:17). Now capped at 3
  attempts / 1s (`tests/test_push_backoff.sh` pins it). Waiting never helped: `pull()`
  already rebases, so a non-fast-forward is fixed on the next attempt, and a push that
  still fails isn't lost — the commit is local and `push_state` reruns next cycle.

**Order matters when diagnosing this:** a stalled reply here means *something between
polls*, so read the gap between the `Done.` line and the next `Fetched` line first. The
handler time is the `Fetched`→`[admin] Msg:` span and is almost never the problem.


## PDF delivery (6 AM IST) — has backstops now

- Path: worker cron → `repository_dispatch`? No — it calls the **workflow dispatch**
  API on `daily.yml`, which runs `daily_words.py`. `daily_words.py` does **not**
  import `telegram_listener.py`; the interactive cutover cannot affect the PDF.
- **The 00:30 UTC run dies outright on a Gemini 503.** Evidence: Sep 23 and Sep 25
  both failed with `503 UNAVAILABLE 'high demand'`, and `generate_with_retry`
  (6 attempts, 5→80s) exhausted its budget. ~1 in 4 days. Nothing retries it.
- Fixed 2026-09-27: backstop crons at **00:50 and 01:40 UTC** re-dispatch
  `daily.yml`. `daily_words.py` writes `.last_pdf_sent` (a date string) *after* a
  confirmed send and exits 0 at startup if it matches today, so a day that already
  succeeded costs one no-op run and can never double-send. The marker is committed
  by `daily.yml`'s `git add -A`.
- `vps_listener.sh` uses an explicit `STATE_FILES` list (not `git add -A`), so it
  will not clobber `.last_pdf_sent`.

## Cloudflare worker deploy traps (both have bitten)

- **A DO migration of `new_classes` blocks *every* deploy on the free plan** with
  `code 10097`; it must be `new_sqlite_classes`. This silently meant the worker
  could not be redeployed from 2026-08-22 until 2026-09-27 — the repo was ahead of
  prod the whole time. Pinned by `tests/test_conductor_crons.py`.
- **A cron in `wrangler.toml` with no `WORKFLOW_MAP` entry** logs
  `Unknown cron trigger` and dispatches nothing — no PDF, no visible error. Also
  pinned by a test.
- `TELEGRAM_CHAT_ID` / `TELEGRAM_GROUP_ID` were never set as worker secrets. With
  `ownerChat == ""` the owner exemption `chatId === ownerChat` can never match, so
  the rate limiter would have rate-limited *the owner* to 1 msg/day on the webhook
  rollback path. Now set (piped from `/etc/vocab-bot.env`, never printed).
  All 5 worker secrets present as of 2026-09-27.
- The webhook rate-limit/whitelist hardening is now **deployed** (it was deferred).
  Inert while the webhook is deleted, and correct if it is ever restored.

## Still open

- `getMyCommands` for the *default* scope returns 400 (`can't parse BotCommandScope`).
  Cosmetic, pre-existing, logs on every cycle. `all_private_chats` works fine.
- `vocab-bot/PENDING.md`: old broad `GITHUB_TOKEN` not yet swapped for a
  fine-grained one (the VPS uses a deploy key, so this is less urgent than it was).

## Repo state
- `vocab-bot` is a git submodule of `D:\Automation`.
- Push order: commit+push `vocab-bot` first (rebase if remote has new auto-commits), then bump submodule pointer in parent `Automation` and push.
- Local branch is `oracle-vps-listener`, which tracks and pushes to `origin/main`.
