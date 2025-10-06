# Meme Stock Tracker

This Python script utilizes the Google Gemini API to generate a daily report on potential "meme stocks." The application is designed for both on-demand execution and automated daily operation through a scheduled task that runs right before the market opens.

## Features

  * **AI-Generated Analysis**: Uses Google's Gemini model with integrated web search grounding to provide reports based on up-to-date information.
  * **Customizable Prompts**: The prompt sent to the AI is fully customizable, allowing users to tailor the content, format, and focus of the generated report.
  * **Task Automation**: For Windows users, the script includes a feature to create and manage a daily scheduled task for fully automated execution.
  * **Configuration Interface**: A command-line menu allows for the management of all settings, including API credentials, scheduling, and output preferences.
  * **Report Output**: Reports are saved to a local `.txt` file and can be optionally displayed in a graphical user interface (GUI) window upon generation.
  * **API Resilience**: Incorporates a retry mechanism with exponential backoff to handle transient API connection failures.

## Installation and Setup

### Recommended Method: Standalone Executable (Windows)

This method is recommended for most users on Windows as it requires no setup of a Python environment.

1.  Download the `.exe` application from the project's official releases page.
2.  Place the executable file in a dedicated directory on your computer.
3.  Run the application. On the first launch, you will be directed to the settings menu to configure your API key.
4.  Secure a Google GenAI API key from the [Google AI for Developers](https://ai.google.dev/) platform.

### Alternate Method: Running from Source

This method is intended for developers or users on other operating systems.

1.  **Prerequisites**: An installation of Python 3.9+ is required.
2.  **Install Dependencies**: Open a terminal or command prompt and execute the following command to install the required libraries:
    ```bash
    pip install google-generativeai Pillow tenacity
    ```
3.  **Obtain an API Key**: Secure a Google GenAI API key from the [Google AI for Developers](https://ai.google.dev/) platform.
4.  **Execute the Script**: Run the script from the command line:
    ```bash
    python meme_stock_tracker.py
    ```

## Usage

Upon launching the application, the main menu provides the following options:

```
==============================================
      Meme Stock Tracker Management
==============================================

  1) Schedule Daily Task
  2) Run Script Now
  3) Settings
  4) Exit
```

  * **Run Script Now**: Immediately queries the Gemini API to generate and save a new report.
  * **Schedule Daily Task**: (Windows only) Creates a Windows Task Scheduler job for automated daily execution.
  * **Settings**: Navigates to a sub-menu for application configuration.

-----

## Configuration Settings

The settings menu allows for the customization of the script's operational parameters. All settings are stored in a `config.ini` file created in the application's directory.

#### 1\. Set/Update Schedule Time (UTC)

Configures the execution time for the daily scheduled task.

  * **Format**: The time must be specified in 24-hour UTC format (e.g., `13:30`).
  * **Rationale**: Using UTC as a standard prevents inconsistencies related to local time zones and Daylight Saving Time. The application converts the UTC time to the system's local time when creating the scheduled task.

#### 2\. Update API Key

Prompts the user to input their Google GenAI API key, which is required for all API communications.

#### 3\. Update GenAI Model

Allows the user to specify a different Gemini model for generating reports. The default is `gemini-2.5-pro`.

#### 4\. View/Edit API Prompt

Opens the current AI prompt in the system's default text editor, enabling full customization of the query sent to the model. The dynamic variable `{today_date}` can be inserted into the prompt to automatically include the current date in the request.

#### 5\. Toggle GUI Pop-up

Enables or disables the Tkinter-based GUI window that displays the report upon generation. Disabling this is recommended for non-interactive, automated runs.

-----

## Important Notes

  * **Platform-Specific Scheduling**: The built-in scheduling feature is implemented using Windows Task Scheduler and is not available on other operating systems. macOS and Linux users must configure a `cron` job or an equivalent utility for automation.
  * **Administrator Privileges**: Creating or modifying a scheduled task on Windows may require the application to be run with administrator privileges.
