<a name="top"></a>
<div align="center">
<img src="./assets/AIHawk.png">

# AIHawk the first Jobs Applier AI Agent

  ![CI](https://github.com/surapuramakhil-org/Job_hunt_assistant/actions/workflows/ci.yml/badge.svg)

**🤖🔍 Your AI-powered job search assistant. Automate applications, get personalized recommendations, and land your dream job faster.**

[![Discord](https://img.shields.io/discord/1300208460788400159?style=for-the-badge&color=5865F2&logo=discord&logoColor=white&label=Discord)](https://discord.gg/MYYwG8JyrQ)

</div>

**Creator** [feder-cr](https://github.com/feder-cr), Co-Founder of AIHawk </br>
As AIHawk is focusing on their proprietary product - solving problems in hiring for companies, currently this project is led, managed, and maintained by a group of open-source contributors, with a focus on building tools to help job seekers land the jobs they deserve.

**Project Maintainers / Leads**: [surapuramakhil](https://github.com/surapuramakhil), [sarob](https://github.com/sarob), [cjbbb](https://github.com/cjbbb)

[Special thanks](#special-thanks) 

Auto_Jobs_Applier_AIHawk is continuously evolving, and your feedback, suggestions, and contributions are highly valued. Feel free to open issues, suggest enhancements, or submit pull requests to help improve the project. Let's work together to make Auto_Jobs_Applier_AIHawk a powerful tool for job seekers worldwide.

## Table of Contents

1. [Introduction](#introduction)
2. [Features](#features)
3. [Installation](#installation)
4. [Configuration](#configuration)
5. [Usage](#usage)
6. [Documentation](#documentation)
7. [Troubleshooting](#troubleshooting)
8. [Conclusion](#conclusion)
9. [Contributors](#contributors)
10. [License](#license)
11. [Disclaimer](#disclaimer)

## Introduction

Auto_Jobs_Applier_AIHawk is a cutting-edge, automated tool designed to revolutionize the job search and application process. In today's fiercely competitive job market, where opportunities can vanish in the blink of an eye, this program offers job seekers a significant advantage. By leveraging the power of automation and artificial intelligence, Auto_Jobs_Applier_AIHawk enables users to apply to a vast number of relevant positions efficiently and in a personalized manner, maximizing their chances of landing their dream job.

### The Challenge of Modern Job Hunting

In the digital age, the job search landscape has undergone a dramatic transformation. While online platforms have opened up a world of opportunities, they have also intensified competition. Job seekers often find themselves spending countless hours scrolling through listings, tailoring applications, and repetitively filling out forms. This process can be not only time-consuming but also emotionally draining, leading to job search fatigue and missed opportunities.

### Enter Auto_Jobs_Applier_AIHawk: Your Personal Job Search Assistant

Auto_Jobs_Applier_AIHawk steps in as a game-changing solution to these challenges. It's not just a tool; it's your tireless, 24/7 job search partner. By automating the most time-consuming aspects of the job search process, it allows you to focus on what truly matters - preparing for interviews and developing your professional skills.

## Features

1. **Intelligent Job Search Automation**
   - Customizable search criteria
   - Continuous scanning for new openings
   - Smart filtering to exclude irrelevant listings

2. **Rapid and Efficient Application Submission**
   - One-click applications
   - Form auto-fill using your profile information
   - Automatic document attachment (resume, cover letter)

3. **AI-Powered Personalization**
   - Dynamic response generation for employer-specific questions
   - Tone and style matching to fit company culture
   - Keyword optimization for improved application relevance

4. **Volume Management with Quality**
   - Bulk application capability
   - Quality control measures
   - Detailed application tracking

5. **Intelligent Filtering and Blacklisting**
   - Company blacklist to avoid unwanted employers
   - Title filtering to focus on relevant positions

6. **Dynamic Resume Generation**
   - Automatically creates tailored resumes for each application
   - Customizes resume content based on job requirements

7. **Secure Data Handling**
   - Manages sensitive information securely using YAML files

## Installation

**Confirmed successful runs on the following:**

- Operating Systems:
  - Windows 10
  - Ubuntu 22
  - macOS
- Python versions:
  - 3.13

## Prerequisites

Before you begin, ensure you have met the following requirements:

### Download and Install Python

Ensure you have the latest Python version installed (Python 3.8 or higher is required for Poetry). If not, download and install it from Python's official website. For detailed instructions, refer to the tutorials:
- [How to Install Python on Windows](https://docs.python.org/3/using/windows.html)
- [How to Install Python on Linux](https://docs.python.org/3/using/unix.html)
- [How to Download and Install Python on macOS](https://docs.python.org/3/using/mac.html)

### Download and Install Google Chrome

Download and install the latest version of Google Chrome in its default location from the [official website](https://www.google.com/chrome/).

### Install Poetry

Follow the instructions provided on Poetry's [official installation page](https://python-poetry.org/docs/#installation).

### Clone the Repository

```bash
git clone https://github.com/surapuramakhil-org/Job_hunt_assistant.git
cd Job_hunt_assistant
```

#### switching to stable versions

place to find release tags: https://github.com/surapuramakhil-org/Job_search_assistant/releases

```bash
git checkout <tag_name>
```

example:
```bash
git checkout v0.1.0-beta
```

### Setting Up the Project with Poetry

Since the project already includes a `pyproject.toml` file, follow these steps:

#### Install Dependencies

Run the following command in the project directory to install all dependencies specified in `pyproject.toml`:

```bash
poetry install
```

### Create `.env` File

To configure environment variables for the project, create a `.env` file by copying the `.env.template` file provided in the repository. This file will store sensitive information such as API keys and other configuration settings.

```bash
cp .env.template .env
```

After copying, open the `.env` file and fill in the required values. Ensure you do not share this file or commit it to version control, as it contains sensitive information.

#### Run the Program

After installing dependencies, run the program using:

```bash
poetry run python src/main.py
```

### For configuration refer [this docs](/docs/configuration.md)
### For troubleshooting refer [this docs](/docs/troubleshooting.md)

## Usage

0. **Account language**
   To ensure the bot works, your account language must be set to English.

1. **Data Folder:**
   Ensure that your data_folder contains the following files:
   - `secrets.yaml`
   - `config.yaml`
   - `plain_text_resume.yaml`

2. **Output Folder:**
    Contains the output of the bot.
    - `data.json` results of the --collect mode
    - `failed.json` failed applications
    - `open_ai_calls.json` all the calls made to the LLM model
    - `skipped.json` applications that were skipped
    - `success.json` successful applications

    **Note:** `answers.json` is not part of the output folder and can be found in the root of the project. It is used to store the answers of the questions asked to the user. Can be used to update the bot with corrected answers. Search for `Select an option`, `0`, `Authorized`, and `how many years of` to verify correct answers.

3. **Run the Bot:**

   Auto_Jobs_Applier_AIHawk offers flexibility in how it handles your pdf resume:

- **Dynamic Resume Generation:**
  If you don't use the `--resume` option, the bot will automatically generate a unique resume for each application. This feature uses the information from your `plain_text_resume.yaml` file and tailors it to each specific job application, potentially increasing your chances of success by customizing your resume for each position.

   ```bash
   poetry run python main.py
   ```

- **Using a Specific Resume:**
  If you want to use a specific PDF resume for all applications, place your resume PDF in the `data_folder` directory and run the bot with the `--resume` option:

  ```bash
  poetry run python main.py --resume /path/to/your/resume.pdf
  ```

- **Using the collect mode:**
  If you want to collect job data only to perform any type of data analytics you can use the bot with the `--collect` option. This will store in output/data.json file all data found from linkedin jobs offers.

  ```bash
  poetry run python main.py --collect
  ```
  
## Documentation

### For Users

- Ollama & Gemini Setup
  - To install and configure **Ollama** and **Gemini**, [Download Ollama and Gemini Setup Guide (PDF)](docs/guide_to_setup_ollama_and_gemini.pdf)
  - Follow the instructions in these guides to ensure proper configuration of **AIHawk** with **Ollama** and **Gemini**.
  - Written by Rushi, [Linkedin](https://www.linkedin.com/in/rushichaganti/), support him by following.

- Editing YAML Files
  - For detailed instructions on editing YAML configuration sections for **AIHawk**, refer to this document:
  - [Download YAML Editing Guide (PDF)](docs/guide_yaml_sections.pdf)
  - Written by Rushi, [Linkedin](https://www.linkedin.com/in/rushichaganti/), support him by following.

- Auto-start AIHawk
  - To make **AIHawk** automatically start when your system boots, follow the steps in this guide:
  - [Download Auto-start AIHawk Guide (PDF)](docs/guide_to_autostart_aihawk.pdf)
  - Written by Rushi, [Linkedin](https://www.linkedin.com/in/rushichaganti/), support him by following.

- Video Tutorial
  - [How to set up Auto_Jobs_Applier_AIHawk](https://youtu.be/gdW9wogHEUM)
  - Written by Rushi, [Linkedin](https://www.linkedin.com/in/rushichaganti/), support him by following.

- [OpenAI API Documentation](https://platform.openai.com/docs/)

### For Developers

- [Contribution Guidelines](docs/CONTRIBUTING.md)

- [Lang Chain Developer Documentation](https://python.langchain.com/v0.2/docs/integrations/components/)

- [Workflow diagrams](docs/workflow_diagrams.md)

- If you encounter any issues, you can open an issue on [GitHub](https://github.com/surapuramakhil-org/Job_hunt_assistant/issues).
  Please add valuable details to the subject and to the description. If you need new feature then please reflect this.  
  I'll be more than happy to assist you!

- Note for Contributors: If you would like to submit a Pull Request (PR), please target the `release` branch instead of `main`. The `release` branch is used for testing new code changes and will be periodically merged into `main` after validation. This approach ensures that only tested features make it into the main branch.

## Conclusion

Auto_Jobs_Applier_AIHawk provides a significant advantage in the modern job market by automating and enhancing the job application process. With features like dynamic resume generation and AI-powered personalization, it offers unparalleled flexibility and efficiency. Whether you're a job seeker aiming to maximize your chances of landing a job, a recruiter looking to streamline application submissions, or a career advisor seeking to offer better services, Auto_Jobs_Applier_AIHawk is an invaluable resource. By leveraging cutting-edge automation and artificial intelligence, this tool not only saves time but also significantly increases the effectiveness and quality of job applications in today's competitive landscape.

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=surapuramakhil-org/Job_hunt_assistant&type=Date)](https://star-history.com/#surapuramakhil-org/Job_hunt_assistant&Date)

If you like the project please star ⭐ the repository!

## Special Thanks
[![Contributors](https://img.shields.io/github/contributors/surapuramakhil-org/Job_hunt_assistant)](https://github.com/surapuramakhil-org/Job_hunt_assistant/graphs/contributors)

<a href="https://github.com/surapuramakhil-org/Job_hunt_assistant/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=surapuramakhil-org/Job_hunt_assistant" />
</a>

Made with [contrib.rocks](https://contrib.rocks).

## License

This project is licensed under the AGPL License. Documentation is licensed under CC BY - see the [AGPL LICENSE](LICENSE) and [CC BY LICENSE](docs/LICENSE) files for details.

The AGPL License requires that any derivative work must also be open source and distributed under the same license.

The CC BY License permits others to distribute, remix, adapt, and build upon your work, even for commercial purposes, as long as they credit you for the original creation. 
 

## Disclaimer

This tool, Auto_Jobs_Applier_AIHawk, is intended for use at your own risk. The creators / maintainers / contributors assume no responsibility for any consequences arising from its use. Users are advised to comply with the terms of service of relevant platforms and adhere to all applicable laws, regulations, and ethical guidelines. The use of automated tools for job applications may carry risks, including potential impacts on user accounts. Proceed with caution and at your own discretion.

[Back to top 🚀](#top)
