# Quick Start Guide

Get your AI Usage Dashboard running in minutes!

## 1. Installation

```bash
# Install dependencies
pip install -r requirements.txt
```

## 2. Configuration

1. Copy the example environment file:
```bash
cp .env.example .env
```

2. Edit `.env` and add your API keys:
```env
OPENAI_API_KEY=your_actual_openai_key_here
ANTHROPIC_API_KEY=your_actual_claude_key_here
MINIMAX_API_KEY=your_actual_minimax_key_here
ZAI_API_KEY=your_actual_zai_key_here
GEMINI_API_KEY=your_actual_gemini_key_here
```

## 3. Run the Application

```bash
# Start the Flask server
python app.py
```

## 4. Access the Dashboard

Open your browser and navigate to:
```
http://localhost:5000
```

## 5. Try the Demo

Run the demonstration file to see all features:
```bash
python demo/demo_usage.py
```

## What You'll See

### Dashboard Features:
- **Real-time usage tracking** for all configured providers
- **Time period filters**: hourly, daily, weekly, monthly
- **Visual progress bars** for usage limits
- **Color-coded status indicators**:
  - 🟢 Green: Within limits
  - 🟡 Yellow: Warning (80%+ of limit)
  - 🔴 Red: Critical (95%+ of limit)
  - ⚫ Gray: Exceeded limit
- **Cost monitoring** with daily cost limits
- **Alert system** for approaching limits

### API Endpoints:
- `GET /api/usage` - Get usage summary
- `GET /api/providers` - List all providers and status
- `GET /api/alerts` - Get current alerts
- `GET /api/history/<provider>` - Get provider history
- `POST /api/config` - Update provider configuration
- `POST /api/test-connection` - Test API key connection

## Customization

### Adding New Providers

Edit `config/providers.json`:

```json
{
  "your_provider": {
    "name": "Your Provider Name",
    "enabled": true,
    "default_model": "model-name",
    "rate_limit_per_minute": 100,
    "rate_limit_per_hour": 4000,
    "rate_limit_per_day": 200000,
    "daily_cost_limit": 50.0
  }
}
```

### Adjusting Limits

Update the rate limits in `config/providers.json` to match your API's actual limits.

## Troubleshooting

### Flask Error: "Import flask could not be resolved"
- Make sure you've installed the requirements: `pip install -r requirements.txt`

### No data appearing
- Check your API keys in `.env` file
- Verify providers are enabled in `config/providers.json`
- Check that API keys are valid by running: `python demo/demo_usage.py`

### API not responding
- Make sure you've started the server with `python app.py`
- Check that Flask is properly configured
- Verify your port 5000 is not in use

## Next Steps

1. Explore the dashboard at `http://localhost:5000`
2. Run the demo script to understand all features: `python demo/demo_usage.py`
3. Customize providers in `config/providers.json`
4. Configure your API keys in `.env`

## Tips

- **Security**: Never commit `.env` file to version control
- **Monitoring**: Set up regular checks for alert notifications
- **Budgeting**: Adjust daily cost limits based on your budget
- **Scaling**: Add more providers as needed for different AI services

## Support

For issues or questions, check:
- README.md for detailed documentation
- API documentation in `app.py` docstrings
- Demo file for examples: `demo/demo_usage.py`
