# QwozVPN Bot Documentation

## Overview
This project contains a Telegram bot for QwozVPN, built with **aiogram 3.x**. The bot provides a main menu, purchase flow, and basic support/profile/help interactions.

## Project Structure
```
app/
  bot/
    data/
      config.py         # Environment-based configuration
    handler/
      user_handler.py   # /start, /help, profile, support, how-to
      payments_handler.py # buy flow callbacks
    keyboard/
      main_menu.py      # main menu inline keyboard
      buy_keyboard.py   # buy flow inline keyboard
    main.py             # bot entrypoint
  client/
    main.py             # placeholder for client-side logic
```

## Configuration
All secrets and runtime values should be set via environment variables.

| Variable | Description | Default |
| --- | --- | --- |
| `BOT_TOKEN` | Telegram bot token | `""` |
| `SUPPORT_USERNAME` | Telegram support username (without @) | `"YourSupportUsername"` |

Example (bash):
```bash
export BOT_TOKEN="123456:ABCDEF..."
export SUPPORT_USERNAME="qwozvpn_support"
```

## Running the Bot
From the repository root:
```bash
python -m app.bot.main
```

## CI/CD
The CI workflow runs on every push and pull request. It installs dependencies,
checks package integrity, and compiles the Python sources to catch syntax errors.
No bot token is required for these checks because they do not start the bot.

### Secrets in CI
If you later add integration tests that need a real token, store it as a GitHub
Actions secret (e.g., `BOT_TOKEN`) and pass it via environment variables in the
workflow. Secrets are masked in logs and are only available to the job runtime;
they do not persist after the workflow finishes.

## Main Features
- **Start menu** with profile, purchase, support, and how‑to actions.
- **Purchase flow** with crypto/card options and a cancel action.
- **Logging** to both stdout and `bot.log`.

## Notes
- Update `SUPPORT_USERNAME` to your actual support handle.
- `app/client/main.py` is currently empty and can be used for future client‑side extensions.
