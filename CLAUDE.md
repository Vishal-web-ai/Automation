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

## Still open

- `getMyCommands` for the *default* scope returns 400 (`can't parse BotCommandScope`).
  Cosmetic, pre-existing, logs on every cycle. `all_private_chats` works fine.
- `vocab-bot/PENDING.md`: CF worker rate-limit/whitelist not deployed; old broad
  `GITHUB_TOKEN` not yet swapped for a fine-grained one (the VPS uses a deploy key, so
  this is less urgent than it was).

## Repo state
- `vocab-bot` is a git submodule of `D:\Automation`.
- Push order: commit+push `vocab-bot` first (rebase if remote has new auto-commits), then bump submodule pointer in parent `Automation` and push.
- Local branch is `oracle-vps-listener`, which tracks and pushes to `origin/main`.
