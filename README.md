# hsim

A comprehensive discrete event simulation (DES) framework designed for manufacturing system modeling, with a specific focus on the GSOM (Global Supply Operations Management) simulation game.

## Features

- **Discrete Event Simulation Engine**: Virtual and real-time simulation support
- **Finite State Machines**: Complex entity behavior modeling
- **Message Passing System**: Asynchronous agent communication
- **Manufacturing Components**: Pre-built servers, buffers, generators, and terminators
- **Web Interface**: Multi-user Flask application with authentication
- **Performance Analysis**: Gantt charts, utilization tracking, and statistical analysis

## Installation

```bash
# Clone the repository
git clone https://github.com/Industry40Lab/hsim.git
cd hsim

# Install dependencies
pip install -r requirements.txt

# Install the package
pip install -e .
```

## Quick Start

### Basic Simulation

```python
from hsim.core.core.env import Environment
from hsim.core.des.pymulate import Generator, Server, Terminator
from hsim.core.agent.agent import Agent

# Create environment
env = Environment()

# Create simulation components
generator = Generator(env, Agent, serviceTime=1)
server = Server(env, serviceTime=2)
terminator = Terminator(env)

# Connect components
generator.connections["next"] = server
server.connections["next"] = terminator

# Run simulation
env.run(until=100)
```

### Running the Flask Application

```bash
cd hsim/GSOM/flask
python app.py
```

The web application will be available at `http://localhost:5000`

## Security Best Practices

### Environment Variables

Create a `.env` file in the project root (never commit this file):

```bash
# Flask Configuration
FLASK_SECRET_KEY=your-secure-random-key-here

# Azure Communication Services
AZURE_CONNECTION_STRING=your-azure-connection-string

# Database Configuration
USERS_DB=hsim/GSOM/flask/static/db/users.db

# Simulation Configuration
USE_GANTT=True
TIMEOUT=180
```

### Password Requirements

When registering users, passwords must meet the following criteria:
- Minimum 8 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one digit

## Project Structure

```
hsim/
├── core/           # Core simulation framework
│   ├── agent/      # Agent base classes
│   ├── core/       # Environment, events, messages
│   ├── des/        # DES building blocks
│   ├── fsm/        # Finite state machines
│   └── utils/      # Utilities and analysis tools
├── GSOM/           # Manufacturing simulation game
│   ├── flask/      # Web application
│   └── ...
├── tests/          # Test suite
└── ...
```

## Running Tests

```bash
python -m pytest tests/
# or
python -m unittest discover tests
```

## Documentation

See [CLAUDE.md](CLAUDE.md) for detailed architecture documentation.

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Authors

- Lorenzo - Initial work

## Acknowledgments

- Built for manufacturing system simulation and Industry 4.0 research
- Supports educational and research applications in supply chain management
