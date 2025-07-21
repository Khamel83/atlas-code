# Atlas Code FAQ for Raspberry Pi Users with OpenRouter

This FAQ is designed to help Raspberry Pi users get started with Atlas Code using a single OpenRouter API key.

## 1. What is Atlas Code?
Atlas Code is an AI pair programming assistant that helps you write, refactor, and understand code directly in your terminal. It leverages large language models (LLMs) to provide intelligent suggestions, generate code, and automate various development tasks.

## 2. Why use Atlas Code on a Raspberry Pi?
The Raspberry Pi is a compact, low-power computer, making it an ideal platform for running personal development tools like Atlas Code. It allows you to have a dedicated AI coding assistant without needing a powerful desktop machine, perfect for learning, hobby projects, or remote development.

## 3. What do I need to get started?
*   **Raspberry Pi:** A Raspberry Pi 4 or newer is recommended for better performance. Ensure it has a stable power supply and sufficient storage (an SD card of 16GB or more is usually fine).
*   **Operating System:** Raspberry Pi OS (formerly Raspbian) is recommended.
*   **Python:** Python 3.9 or newer is required. It usually comes pre-installed on Raspberry Pi OS.
*   **OpenRouter API Key:** You'll need an API key from OpenRouter to access various LLMs.
*   **Internet Connection:** Required for installing packages and communicating with LLMs.

## 4. How do I install Atlas Code on my Raspberry Pi?

1.  **Update your system:**
    ```bash
    sudo apt update
    sudo apt upgrade -y
    ```
2.  **Install `pip` (if not already installed):**
    ```bash
    sudo apt install python3-pip -y
    ```
3.  **Install Atlas Code:**
    ```bash
    python3 -m pip install atlas-code
    ```
    *Note: If you encounter issues, ensure your `pip` is up-to-date: `python3 -m pip install --upgrade pip`*

## 5. How do I configure Atlas Code with my OpenRouter API Key?

1.  **Get your OpenRouter API Key:**
    *   Go to the OpenRouter website (openrouter.ai).
    *   Sign up or log in.
    *   Navigate to your API keys section (usually under your profile or settings).
    *   Generate a new API key and copy it. **Keep this key secure and do not share it publicly.**

2.  **Set the API Key as an Environment Variable:**
    The most secure way to use your API key is by setting it as an environment variable.
    ```bash
    echo 'export OPENROUTER_API_KEY="YOUR_OPENROUTER_API_KEY_HERE"' >> ~/.bashrc
    source ~/.bashrc
    ```
    *Replace `YOUR_OPENROUTER_API_KEY_HERE` with your actual key.*
    *For persistent access, add this line to your shell's profile file (e.g., `~/.bashrc`, `~/.zshrc`).*

## 6. How do I run Atlas Code?

Once installed and configured, you can run Atlas Code from your terminal:

```bash
atlas-code
```

To specify a model (e.g., a Gold/Mid-tier model like DeepSeek Chat):
```bash
atlas-code --model deepseek/deepseek-chat
```

## 7. What are the different model tiers (Silver, Gold, Platinum, Diamond)?

Atlas Code categorizes LLMs into tiers to help you choose the right model for your task, balancing performance and cost:

*   **Silver / Low Tier:** These models are fast and cost-effective, ideal for quick, simple tasks, initial drafting, or when you need many iterations. (e.g., `openrouter/deepseek/deepseek-r1:free`, `o1-mini`)
*   **Gold / Mid Tier:** A good balance of capability and efficiency, suitable for general coding tasks, refactoring, and more complex problem-solving. (e.g., `deepseek/deepseek-chat`, `llama3-70b`)
*   **Platinum / Top Tier:** High-performance models designed for complex analysis, architectural planning, and critical code generation where accuracy and advanced reasoning are crucial. (e.g., `gpt-4o`, `claude-3-5-sonnet`)
*   **Diamond / Flagship Tier:** The most powerful and capable models, reserved for the most demanding tasks, cutting-edge research, and situations requiring the highest level of intelligence. (e.g., `claude-opus-4`, `qwen3-235b`)

You can specify the model using the `--model` flag. Atlas Code will attempt to select an appropriate model if you don't specify one, especially if you're using OpenRouter.

## 8. Troubleshooting and Performance Tips for Raspberry Pi

*   **"Out of Memory" Errors:**
    *   **Increase Swap Space:** While not ideal for performance, increasing swap can prevent crashes. Edit `/etc/dphys-swapfile` and increase `CONF_SWAPSIZE`.
    *   **Reduce GPU Memory:** If you're not using a display, reduce the GPU memory allocation in `raspi-config` (e.g., to 16MB).
    *   **Close Other Applications:** Ensure no other memory-intensive applications are running.
    *   **Use Smaller Models:** Opt for Silver or Gold tier models, as they consume less memory.
*   **Slow Performance:**
    *   **Use Smaller Models:** Lower-tier models are generally faster and less resource-intensive.
    *   **Optimize Python Code:** Ensure your Python environment is optimized. Avoid unnecessary loops or inefficient data structures in your own scripts if you're integrating Atlas Code.
    *   **Overclocking (Advanced):** You can mildly overclock your Raspberry Pi's CPU for better performance, but be mindful of heat. Ensure proper cooling (heatsinks/fans).
    *   **Disable Unnecessary Services:** Turn off services you don't need (e.g., Bluetooth, Wi-Fi if using Ethernet) to free up CPU cycles.
*   **API Key Not Recognized:**
    *   Double-check that `OPENROUTER_API_KEY` is correctly set in your environment. Restart your terminal after adding it to `~/.bashrc` or `~/.zshrc`.
    *   Ensure there are no extra spaces or characters around your API key in the environment variable.
*   **Internet Connectivity Issues:**
    *   Verify your Raspberry Pi has a stable internet connection.
    *   Check OpenRouter's status page for any service outages.

## 9. Where can I find more help?
*   **Atlas Code Documentation:** [Link to main documentation, once branding is updated]
*   **OpenRouter Documentation:** [Link to OpenRouter docs]
*   **Community Support:** [Link to Discord/GitHub Discussions, once branding is updated]
