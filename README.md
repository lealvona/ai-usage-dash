# AI Usage Dashboard

A comprehensive AI usage tracking and visualization dashboard that monitors API usage across multiple AI providers with configurable time-based metrics.

## Features

- **Multi-Provider Support**: Track usage for OpenAI, Claude, Mini Max, Z.ai, and Gemini
- **Extensible Architecture**: Easily add new providers through plugin system
- **Flexible Time Metrics**: View usage data by hourly, daily, weekly, and monthly periods
- **Usage Limits Tracking**: Monitor and alert when approaching provider quotas
- **Configurable API Keys**: Secure management of API credentials
- **Visualization**: Comprehensive dashboards and charts

## Supported Providers

- **OpenAI**: GPT-3.5, GPT-4, GPT-4 Turbo
- **Anthropic Claude**: Claude 2, Claude Instant
- **Mini Max**: Mini Max API services
- **Z.ai**: Z.ai platform integration
- **Gemini**: Google's Gemini models

## Getting Started

### Prerequisites

- Node.js 18+ or Python 3.9+
- npm or yarn

### Installation

```bash
# Clone or navigate to the project
cd ai-usage-dash

# Install dependencies
npm install
# or
pip install -r requirements.txt
```

### Configuration

1. Create a `.env` file in the root directory:
```env
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key
MINIMAX_API_KEY=your_minimax_key
ZAI_API_KEY=your_zai_key
GEMINI_API_KEY=your_gemini_key
```

2. Configure provider settings in `config/providers.json`

### Running the Application

```bash
# Development server
npm run dev
# or
python app.py
```

Access the dashboard at `http://localhost:3000`

## API Key Security

API keys are stored in environment variables and never committed to version control. Use the `.env` file for configuration.

## Project Structure

```
ai-usage-dash/
├── config/
│   └── providers.json        # Provider configurations
├── providers/                # Provider implementations
│   ├── base_provider.py     # Base provider class
│   ├── openai_provider.py
│   ├── claude_provider.py
│   ├── minimax_provider.py
│   ├── zai_provider.py
│   └── gemini_provider.py
├── api/                      # API endpoints
├── dashboards/               # Dashboard components
├── metrics/                  # Usage metrics calculation
├── storage/                  # Data storage
├── demo/                     # Demonstration files
├── .env.example              # Example environment file
└── README.md
```

## Adding New Providers

To add a new AI provider:

1. Create a new file in `providers/` directory
2. Extend the base provider class
3. Implement required methods for usage tracking
4. Update provider registry in `config/providers.json`

## Usage Limits

Each provider has configurable usage limits:
- **OpenAI**: Rate limits based on model tier
- **Claude**: Token limits per minute/hour
- **Mini Max**: Request rate limits
- **Z.ai**: Provider-specific quotas
- **Gemini**: Daily/weekly usage caps

## Demo

See `demo/` directory for demonstration files and examples.

## License

MIT License
