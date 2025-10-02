import os
import sys
import datetime
import configparser
import subprocess
import tkinter as tk
from tkinter import scrolledtext
import tempfile
from typing import Optional
from tenacity import retry, stop_after_attempt, wait_exponential

try:
    from PIL import Image, ImageTk
except ImportError:
    print("ERROR: 'Pillow' library not found. Please run: pip install Pillow")
    sys.exit(1)

try:
    from zoneinfo import ZoneInfo
except ImportError:
    print("Warning: 'zoneinfo' library not found. Timezone features may fail.")
    print("If you are on Python < 3.9, run: pip install tzdata")
    ZoneInfo = None

DEFAULT_PROMPT_TEMPLATE = (
    "Pre-open {today_date}, list 10 likely meme stocks today. Browse, cite, and rank by buzz + "
    "squeeze risk + fresh catalyst. Give a compact table: Ticker, pre-mkt move/vol, short interest %, "
    "days-to-cover, borrow fee/utilization, options vol & put/call, retail-mention trend, catalyst note, "
    "risk flags. Then 3 runners-up and 3 bullet ‘watch items’ (levels/halts)."
)
DEFAULT_MODEL = "gemini-2.5-pro"
DEFAULT_SCHEDULE_TIME_UTC = "13:25"

def get_base_path() -> str:
    """
    Gets the reliable base path, whether running as a script or a frozen executable.

    Returns:
        str: The absolute path to the base directory.
    """
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

def resource_path(relative_path: str) -> str:
    """
    Get absolute path to a resource, works for both development and PyInstaller.

    Args:
        relative_path (str): The relative path to the resource.

    Returns:
        str: The absolute path to the resource.
    """
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def get_config_value(section: str, key: str, fallback: Optional[str] = None) -> Optional[str]:
    """
    Reads a specific value from the config.ini file.

    Args:
        section (str): The section in the config file.
        key (str): The key within the section.
        fallback (Optional[str]): The default value to return if the key is not found.

    Returns:
        Optional[str]: The value from the config file, or the fallback if not found.
    """
    try:
        config_path = os.path.join(get_base_path(), 'config.ini')
        if not os.path.exists(config_path):
            return fallback
        config = configparser.ConfigParser(interpolation=None)  # Disable interpolation
        config.read(config_path)
        return config.get(section, key, fallback=fallback)
    except configparser.Error as e:
        print(f"Error reading config: {e}")
        return fallback

def set_config_value(section: str, key: str, value: str) -> bool:
    """
    Writes a specific value to the config.ini file.

    Args:
        section (str): The section in the config file.
        key (str): The key to write.
        value (str): The value to associate with the key.

    Returns:
        bool: True if the value was written successfully, False otherwise.
    """
    try:
        config_path = os.path.join(get_base_path(), 'config.ini')
        config = configparser.ConfigParser(interpolation=None)  # Disable interpolation
        config.read(config_path)
        if not config.has_section(section):
            config.add_section(section)
        config.set(section, key, value)
        with open(config_path, 'w') as configfile:
            config.write(configfile)
        return True
    except (configparser.Error, IOError) as e:
        print(f"Error writing to config: {e}")
        return False

def edit_prompt() -> None:
    """
    Opens the current prompt in the default text editor for modification.

    Allows the user to edit the prompt template and saves the changes back to the config file.
    """
    current_prompt = get_config_value('Prompt', 'TEMPLATE', fallback=DEFAULT_PROMPT_TEMPLATE)

    try:
        with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix=".txt", encoding='utf-8') as temp_file:
            temp_file.write(current_prompt)
            temp_filepath = temp_file.name
        print("\n Here is the current prompt:\n")
        print("-" * 40)
        print(current_prompt)
        print("-" * 40)
        print("\nOpening prompt in your default text editor...")
        print("\nUse {today_date} in your prompt to insert today's date automatically.")
        print("Please save your changes and close the editor to continue.")

        if sys.platform == "win32":
            os.startfile(temp_filepath)
        elif sys.platform == "darwin":
            subprocess.run(["open", temp_filepath], check=True)
        else:
            subprocess.run(["xdg-open", temp_filepath], check=True)

        input("\nPress Enter here after you have saved and closed the text editor...")

        with open(temp_filepath, 'r', encoding='utf-8') as f:
            new_prompt = f.read().strip()

        if not new_prompt:
            print("\nPrompt is empty. No changes made.")
        elif new_prompt == current_prompt:
            print("\nNo changes detected in the prompt.")
        elif set_config_value('Prompt', 'TEMPLATE', new_prompt):
            print("\nSUCCESS: Prompt template has been updated successfully!")
            print("Here is the new prompt:\n")
            print("-" * 40)
            print(new_prompt)
            print("-" * 40)
        else:
            print("\nERROR: Failed to update the prompt in the configuration file.")

    except Exception as e:
        print(f"\nAn error occurred while trying to edit the prompt: {e}")
    finally:
        if 'temp_filepath' in locals() and os.path.exists(temp_filepath):
            os.remove(temp_filepath)

    input("\nPress Enter to return to the menu...")

def update_api_key() -> None:
    """
    Prompts the user for a new API key and saves it to the config.ini file.
    """
    new_key = input("Please enter your new Google GenAI API key: ").strip()
    if not new_key:
        print("\nAPI key cannot be empty. No changes made.")
    elif set_config_value('API', 'KEY', new_key):
        print("\nSUCCESS: API key has been updated successfully!")
    else:
        print("\nERROR: Failed to update API key.")
    input("\nPress Enter to return to the menu...")

def update_model() -> None:
    """
    Prompts the user for a new GenAI model and saves it to the config.ini file.
    """
    current_model = get_config_value('API', 'MODEL', fallback=DEFAULT_MODEL)
    print(f"\nThe current GenAI model is: {current_model}")
    new_model = input("Enter the new model name (e.g., gemini-2.5-pro): ").strip()

    if not new_model:
        print("\nModel name cannot be empty. No changes made.")
    elif set_config_value('API', 'MODEL', new_model):
        print("\nSUCCESS: GenAI model has been updated successfully!")
    else:
        print("\nERROR: Failed to update the model name.")
    input("\nPress Enter to return to the menu...")

def update_schedule_time() -> None:
    """
    Prompts the user for a new schedule time in UTC and saves it to the config.ini file.
    """
    current_time = get_config_value('Scheduler', 'TIME_UTC', fallback=DEFAULT_SCHEDULE_TIME_UTC)
    print(f"\nThe current scheduled time is {current_time} UTC.")
    time_str = input("Enter the new time to run daily (24-hour UTC format, e.g., 13:30): ").strip()
    try:
        datetime.datetime.strptime(time_str, '%H:%M')
        if set_config_value('Scheduler', 'TIME_UTC', time_str):
            print(f"\nSUCCESS: Schedule time updated to {time_str} UTC.")
            print("Applying new schedule now...")
            schedule_task(pause_on_completion=False)
        else:
            print("\nERROR: Failed to save the new time.")
    except ValueError:
        print("\nInvalid format or time. Please use HH:MM format (e.g., 09:25 or 14:00).")
    
    input("\nPress Enter to return to the menu...")

def schedule_task(pause_on_completion: bool = True) -> None:
    """
    Creates a Windows scheduled task based on the UTC time in config.ini.

    Args:
        pause_on_completion (bool): If True, waits for user input before returning.
    """
    if sys.platform != "win32":
        print("\nTask scheduling is only supported on Windows.")
        if pause_on_completion:
            input("\nPress Enter to return to the menu...")
        return

    utc_time_str = get_config_value('Scheduler', 'TIME_UTC', fallback=DEFAULT_SCHEDULE_TIME_UTC)
    if not utc_time_str:
        print("\nNo schedule time is set. Please use the menu to set a time first.")
        if pause_on_completion:
            input("\nPress Enter to return to the menu...")
        return

    try:
        hour, minute = map(int, utc_time_str.split(':'))
        local_tz = datetime.datetime.now().astimezone().tzinfo
        now_utc = datetime.datetime.now(datetime.timezone.utc)
        target_utc = now_utc.replace(hour=hour, minute=minute, second=0, microsecond=0)
        local_time = target_utc.astimezone(local_tz)
        local_time_str = local_time.strftime('%H:%M')

        executable_path = sys.executable
        task_name = "DailyMemeStockReport"

        if getattr(sys, 'frozen', False):
            task_action = f'"{executable_path}" run'
        else:
            script_path = os.path.abspath(__file__)
            task_action = f'"{executable_path}" "{script_path}" run'

        print(f"\nAttempting to schedule task for {utc_time_str} UTC ({local_time_str} your time)...")
        command = ['schtasks', '/create', '/sc', 'DAILY', '/tn', task_name, '/tr', task_action, '/st', local_time_str, '/f']
        subprocess.run(command, capture_output=True, text=True, check=True, shell=True)
        print(f"SUCCESS: Task '{task_name}' scheduled successfully!")
    except subprocess.CalledProcessError as e:
        print("\nERROR: Failed to create the scheduled task. Try running as Administrator.")
        print(f"Details: {e.stderr}")
    except ValueError as e:
        print(f"\nERROR: Invalid time format in configuration: {utc_time_str}. Error: {e}")
    except Exception as e:
        print(f"\nAn unexpected error occurred during scheduling: {e}")

    if pause_on_completion:
        input("\nPress Enter to return to the menu...")

@retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=1, min=4, max=10))
def _call_gemini_api(client, gemini_model, prompt, config):
    """
    Makes the API call to the Gemini API with retries in case of failure.

    Args:
        client: The Gemini API client.
        gemini_model: The model to use for the API call.
        prompt: The prompt to send to the API.
        config: The configuration for the API call.

    Returns:
        The response from the API.

    Raises:
        Any exception raised by the API call.
    """
    return client.models.generate_content(
        model=gemini_model,
        contents=prompt,
        config=config,
    )

def get_meme_stocks() -> None:
    """
    Connects to the Google Gemini API to get a list of likely meme stocks.
    Saves the report to a file and optionally displays it in a GUI window.
    """
    try:
        from google import genai
        from google.genai import types
    except ImportError:
        print("\nERROR: 'google-generativeai' not installed. Run: pip install google-generativeai")
        return

    api_key = get_config_value('API', 'KEY')
    if not api_key or api_key == 'YOUR_API_KEY_HERE':
        print("\nERROR: API key not set. Please go to Settings to add your key.")
        if not (len(sys.argv) > 1 and sys.argv[1] == 'run'):
            input("\nPress Enter to return to the menu...")
        return

    try:
        prompt_template = get_config_value('Prompt', 'TEMPLATE', fallback=DEFAULT_PROMPT_TEMPLATE)
        gemini_model = get_config_value('API', 'MODEL', fallback=DEFAULT_MODEL)
        today_date = datetime.date.today().strftime("%Y-%m-%d")

        prompt = prompt_template.format(today_date=today_date)

        print(f"\nGenerating meme stock report for {today_date} using model '{gemini_model}'...")

        client = genai.Client(api_key=api_key)
        grounding_tool = types.Tool(google_search=types.GoogleSearch())
        config = types.GenerateContentConfig(tools=[grounding_tool])

        # Use the retry-enabled function to make the API call
        response = _call_gemini_api(client, gemini_model, prompt, config)

        output_text = response.text

        output_file_path = os.path.join(get_base_path(), f"{today_date}_MemeStock.txt")
        with open(output_file_path, "w", encoding="utf-8") as file:
            file.write(output_text)
        print(f"SUCCESS: Report saved to '{output_file_path}'")

        show_gui = get_config_value('Settings', 'SHOW_GUI', fallback='true').lower() == 'true'
        if show_gui:
            _display_report_gui(output_text, today_date)
        else:
            print("GUI pop-up is disabled in settings. The report is in the text file.")

    except genai.exceptions.APIError as e:
        print(f"\nERROR: API call failed. Details: {e}")
    except KeyError as e:
        print(f"\nERROR: Missing key in configuration. Details: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

def _display_report_gui(report_text: str, date_str: str) -> None:
    """
    Displays the generated report in a simple Tkinter GUI window.

    Args:
        report_text (str): The text of the report to display.
        date_str (str): The date string for the window title.
    """
    try:
        print("Displaying report in GUI window...")
        root = tk.Tk()
        root.title(f"Meme Stock Report - {date_str}")
        root.geometry("850x650")

        text_area = scrolledtext.ScrolledText(root, wrap=tk.WORD, font=("Consolas", 12))
        text_area.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        text_area.insert(tk.INSERT, report_text)
        text_area.config(state='disabled')

        root.mainloop()
    except tk.TclError as e:
        print(f"\nERROR: Could not display GUI. Your environment may not support Tkinter.")
        print(f"Details: {e}")
    except Exception as e:
        print(f"\nAn unexpected error occurred with the GUI: {e}")

def toggle_gui():
    """Toggles the GUI pop-up setting in the config file."""
    current_setting_str = get_config_value('Settings', 'SHOW_GUI', fallback='true')
    is_enabled = current_setting_str.lower() == 'true'
    new_setting = 'false' if is_enabled else 'true'
    
    if set_config_value('Settings', 'SHOW_GUI', new_setting):
        status = "DISABLED" if is_enabled else "ENABLED"
        print(f"\nSUCCESS: GUI pop-up has been {status}.")
    else:
        print("\nERROR: Failed to update the GUI setting.")
    input("\nPress Enter to return to the menu...")

def show_cookie_easter_egg():
    IMAGE_PATH = resource_path("dog.jpg")
    PADDING = 200

    try:
        root = tk.Tk()
        root.title("Scaled Image")
        img = Image.open(IMAGE_PATH)
        max_size = (
            root.winfo_screenwidth() - PADDING,
            root.winfo_screenheight() - PADDING
        )
        img.thumbnail(max_size, Image.Resampling.LANCZOS)
        img_tk = ImageTk.PhotoImage(img)
        label = tk.Label(root, image=img_tk)
        label.image = img_tk
        label.pack()
        root.mainloop()
    except FileNotFoundError:
        print(f"\nOops! The easter egg image ('dog.jpg') was not found.")
        input("Press Enter to continue...")
    except Exception as e:
        print(f"\nAn error occurred with the easter egg: {e}")
        input("Press Enter to continue...")

def settings_menu():
    """Displays a sub-menu for editing configuration settings."""
    while True:
        print("\n" + "="*46)
        print("                 Settings Menu")
        print("="*46 + "\n")
        print("  1) Set/Update Schedule Time (UTC)")
        print("  2) Update API Key")
        print("  3) Update GenAI Model")
        print("  4) View/Edit API Prompt")
        print("  5) Toggle GUI Pop-up")
        print("  6) Back to Main Menu\n")

        choice = input("Please enter your choice (1-6): ").strip()

        if choice == '1':
            update_schedule_time()
        elif choice == '2':
            update_api_key()
        elif choice == '3':
            update_model()
        elif choice == '4':
            edit_prompt()
        elif choice == '5':
            toggle_gui()
        elif choice == '6':
            break
        else:
            print("Invalid selection. Please try again.")

def main_menu():
    """Displays the main menu and handles user input for interactive sessions."""
    while True:
        print("\n" + "="*46)
        print("      Meme Stock Tracker Management      ")
        print("="*46 + "\n")
        print("  1) Schedule Daily Task")
        print("  2) Run Script Now")
        print("  3) Settings")
        print("  4) Exit\n")
        
        choice = input("Please enter your choice (1-4): ").strip()

        if choice == '1':
            schedule_task()
        elif choice == '2':
            get_meme_stocks()
        elif choice == '3':
            settings_menu()
        elif choice == '4':
            print("Exiting.")
            break
        elif choice.lower() == 'cookie':
            show_cookie_easter_egg()
        else:
            print("Invalid selection. Please try again.")

if __name__ == "__main__":
    # This block checks if the script was launched with the 'run' argument,
    # which is used by the Task Scheduler for automatic, non-interactive execution.
    if len(sys.argv) > 1 and sys.argv[1] == 'run':
        # If the 'run' argument is present, bypass the menu and execute the core function.
        print(f"Automated run initiated at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        get_meme_stocks()
        print("Automated run complete.")
        # Ensure the script terminates cleanly after the automated task is done.
        sys.exit(0)
    else:
        # If no 'run' argument is found, start the interactive main menu for manual use.
        main_menu()