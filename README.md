# Discord AutoFAQ
This bot written in `python` makes use of a *machine learning* classifier to detect messages in a Discord channel which can be answered with a predefined FAQ.

# How it works
As the administrator, you first have to create an FAQ topic by using `/faq_enable`. Then, you can create FAQ entries with `/faq_add` and fill them with messages which should be automatically answered with your FAQ.

# Commands
| **Command**  | **Description**                                                                                                                                                                                                  | **Permission** |
|--------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------|
| /faq_enable  | Enables AutoFAQ for a Discord channel (and creates an FAQ topic).                                                                                                                                                | use_slash_commands              |
| /faq_disable | Disables AutoFAQ for a Discord channel.                                                                                                                                                                          | use_slash_commands              |
| /faq         | Shows all FAQ entries for a specific topic.                                                                                                                                                                      | use_slash_commands              |
| /faq_add     | Creates an FAQ entry for a specific topic.                                                                                                                                                                       | use_slash_commands              |
| /faq_edit    | Edits an FAQ entry for a specific topic.                                                                                                                                                                         | use_slash_commands              |
| /faq_delete  | Deletes an FAQ entry for a specific topic.                                                                                                                                                                       | administrator  |
| /faq_expand  | Searches for messages in a channel that would be classified as question and then asks the administrator whether this messages should be added to the FAQ entry dataset or ignored. This improves the classifier. | use_slash_commands              |
| /faq_reload  | Reloads every classifier for each topic.                                                                                                                                                                         | use_slash_commands              |
| /save_chat   | Saves `n` messages to a file to improve the non-question dataset to ignore irrelevant messages.                                                                                                                  | administrator  |

# In-Chat Commands
| **Command**                 | **With reference to another message** | **Description**                                                                                                | **Permission**    |
|-----------------------------|---------------------------------------|----------------------------------------------------------------------------------------------------------------|-------------------|
| @AutoFAQ \<faq-abbreviation> | Yes                                   | Posts the answer of your FAQ entry to the referenced message and adds the referenced message to your dataset.  | use_slash_commands |
| @AutoFAQ \<faq-abbreviation> | No                                    | Posts the answer of your FAQ entry.                                                                            | use_slash_commands |
| @AutoFAQ ignore             | Yes                                   | Adds the referenced message to the ignore-dataset and deletes any old FAQ response referenced to that message. | use_slash_commands |

# Requirements
* Python installed
* pip
* a server to run this bot

# Bot Installation
1. Open the [Discord Developer Portal](https://discord.com/developers/applications)
2. Create a new application
3. Add a bot to your application
4. Enable the `message content intent` (used for automatically checking messages)
5. Create an OAuth2 link with following permissions **and the scope bot**
    * Read Messages/View Channels
    * Send Messages
    * Read Message History
    * Add Reactions
6. Connect your bot to your server

# Run your Bot
1. [Download](https://github.com/erikzimmermann/discord-auto-faq/archive/refs/heads/main.zip) the source code of this bot
2. Install all requirements of the bot with `pip install -r requirements.txt`
3. Run the bot with `python bot.py`
