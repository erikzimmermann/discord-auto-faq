# Discord AutoFAQ
This bot written in `python` makes use of *machine learning* to detect messages in a Discord channel which can be answered with a predefined FAQ. 
In order to achieve this, the bot uses **BERT** for natural language processing (**NLP**) to calculate sentence similarities between FAQ triggers and new posted messages. 
Now, if the highest calculated metric for a message exceeds a threshold, the bot automatically reacts with a predefined answer corresponding to the trigger.

If you are interested in BERT, here are 2 links for you:  
* Blog post: [BERT For Measuring Text Similarity](https://towardsdatascience.com/bert-for-measuring-text-similarity-eec91c6bf9e1)  
* Releasing paper: [Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks](https://arxiv.org/abs/1908.10084)  

# Setup
As the administrator, you first have to create an FAQ topic by using `/faq_enable`. Then, you can create FAQ entries with `/faq_add` and fill them with messages which should be automatically answered with your FAQ.

# Commands
| **Command**  | **Description**                                                   | **Permission**   |
|--------------|-------------------------------------------------------------------|------------------|
| /faq_help    | Displays the most relevant things to know for staff members.      | moderate_members |
| /faq_enable  | Enables AutoFAQ for a Discord channel (and creates an FAQ topic). | moderate_members |
| /faq_disable | Disables AutoFAQ for a Discord channel.                           | moderate_members |
| /faq         | Shows all FAQ entries for a specific topic.                       | moderate_members |
| /faq_add     | Creates an FAQ entry for a specific topic.                        | moderate_members |
| /faq_edit    | Edits an FAQ entry for a specific topic.                          | moderate_members |
| /faq_delete  | Deletes an FAQ entry for a specific topic.                        | administrator    |
| /faq_reload  | Reloads every classifier for each topic.                          | moderate_members |

# In-Chat Commands
| **Command**                  | **With reference to another message** | **Description**                                                                                                | **Permission**   |
|------------------------------|---------------------------------------|----------------------------------------------------------------------------------------------------------------|------------------|
| @AutoFAQ \<faq-abbreviation> | Yes                                   | Posts the answer of your FAQ entry to the referenced message and adds the referenced message to your dataset.  | moderate_members |
| @AutoFAQ \<faq-abbreviation> | No                                    | Posts the answer of your FAQ entry.                                                                            | moderate_members |
| @AutoFAQ ignore              | Yes                                   | Adds the referenced message to the ignore-dataset and deletes any old FAQ response referenced to that message. | moderate_members |

# Requirements
* python installed
* pip
* a server to run this bot
  * The bot requires at most times ~350MB RAM to load the classifier and 
  * ~3GB disk space to be able to install required libraries.

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
