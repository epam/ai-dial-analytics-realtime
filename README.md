# Overview

Realtime analytics server for [AI DIAL](https://epam-rail.com). The service consumes the logs stream [AI DIAL Core](https://github.com/epam/ai-dial-core), analyzes the conversation and writes the analytics to the [InfluxDB](https://www.influxdata.com/).

# Usage

Check the [AI DIAL Core](https://github.com/epam/ai-dial-core) documentation to configure the way to send the logs to the instance of the realtime analytics server.

The realtime analytics server analyzes the logs stream in the realtime and writes the metric `analytics` to the InfluxDB with the following data:

|Tag|Description|
|---|---|
|model| The model name for the completion request. |
|deployment| The deployment name of the model or application for the completion request. |
|project_id| The project ID for the completion request |
|language| The language of the conversation detected by the messages content. |
|topic| The topic of the conversation detected by the messages content. |
|title| The title of the person making the request. |
|response_id| Unique ID of this response. |

|Field|Description|
|---|---|
|user_hash| The unique hash for the user. |
|price| The calculated price of the request. |
|number_request_messages| The total number of messages in history for this request. |
|chat_id| The unique ID of this convestation. |
|prompt_tokens| The number of tokens in the prompt including conversation history and the current message |
|completion_tokens| The number of completion tokens generated for this request |


# Configuration

Copy `.env.example` to `.env` and customize it for your environment.

### Connection to the InfluxDB
You need to specify the connection options to the InfluxDB instance using the environment variables:
|Variable|Description|
|---|---|
|INFLUX_URL|Url to the InfluxDB to write the analytics data |
|INFLUX_ORG| Name of the InfluxDB organization to write the analytics data |
|INFLUX_BUCKET| Name of the bucket to write the analytics data  |
|INFLUX_API_TOKEN| InfluxDB API Token |

You can follow the [InfluxDB documentation](https://docs.influxdata.com/influxdb/v2/get-started/) to setup InfluxDB locally and acquire the required configuration parameters.

### Other configuration
Also, following environment valuables can be used to configure the service behavior:

|Variable|Default|Description|
|---|---|---|
|MODEL_RATES| {} | Specifies per-token price rates for models in JSON format|

Example of the MODEL_RATES configuration:
```json
{
    "gpt-4": {
        "unit":"token",
        "prompt_price":"0.00003",
        "completion_price":"0.00006"
    },
    "gpt-35-turbo": {
        "unit":"token",
        "prompt_price":"0.0000015",
        "completion_price":"0.000002"
    },
    "gpt-4-32k": {
        "unit":"token",
        "prompt_price":"0.00006",
        "completion_price":"0.00012"
    },
    "text-embedding-ada-002": {
        "unit":"token",
        "prompt_price":"0.0000001"
    },
    "chat-bison@001": {
        "unit":"char_without_whitespace",
        "prompt_price":"0.0000005",
        "completion_price":"0.0000005"
    }
}
```


______
# Developer environment

This project uses [Python>=3.11](https://www.python.org/downloads/) and [Poetry>=1.6.1](https://python-poetry.org/) as a dependency manager. 
Check out Poetry's [documentation on how to install it](https://python-poetry.org/docs/#installation) on your system before proceeding.

To install requirements:

```
poetry install
```

This will install all requirements for running the package, linting, formatting and tests.

# Build

To build the wheel packages run:
```sh
make build
```

# Run

To run the development server locally run:

```sh
make serve
```

The server will be running as http://localhost:5001

# Docker

To build the docker image run:
```sh
make docker_build
```

To run the server locally from the docker image run:
```sh
make docker_serve
```

The server will be running as http://localhost:5001

# Lint

Run the linting before committing:

```sh
make lint
```

To auto-fix formatting issues run:

```sh
make format
```

# Test

Run unit tests locally:

```sh
make test
```

# Clean

To remove the virtual environment and build artifacts:

```sh
make clean
```
