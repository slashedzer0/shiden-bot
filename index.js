require('dotenv').config();
console.log('Bot token:', process.env.TELEGRAM_BOT_TOKEN);

const TelegramBot = require('node-telegram-bot-api');
const axios = require('axios');

// Create a new bot instance
const bot = new TelegramBot(process.env.TELEGRAM_BOT_TOKEN, { polling: true });

// Define a function to download media from an Instagram post URL
async function downloadMedia(url) {
  // Make a GET request to the Instagram post URL and extract the HTML response
  const response = await axios.get(url);

  // Extract the metadata JSON object from the HTML response
  const metadata = response.data.match(/<script type="text\/javascript">window\._sharedData = (.+);<\/script>/)[1];
  const { entry_data: { PostPage: [ postPage ] } } = JSON.parse(metadata);

  // Determine if the post is an image or video
  let type, urlData;
  if (postPage.graphql.shortcode_media.__typename === 'GraphVideo') {
    // If the post is a video, extract the highest-quality version of the video
    const { video_url: videoUrl } = postPage.graphql.shortcode_media;
    const { data: videoData } = await axios.get(videoUrl, { responseType: 'arraybuffer' });
    type = 'video';
    urlData = videoData;
  } else if (postPage.graphql.shortcode_media.__typename === 'GraphImage') {
    // If the post is an image, extract the image URL
    const { display_url: imageUrl } = postPage.graphql.shortcode_media;
    const { data: imageData } = await axios.get(imageUrl, { responseType: 'arraybuffer' });
    type = 'image';
    urlData = imageData;
  } else {
    // If the post is not a video or image, throw an error
    throw new Error('Invalid Instagram post type');
  }

  // Return the media data and type
  return { type, data: urlData };
}

// Create a new event listener that listens for the /start command and sends a welcome message to the user
bot.onText(/\/start/, (msg) => {
  bot.sendMessage(msg.chat.id, 'Welcome to the Instagram media downloader bot! To download an image or video, simply paste the post link.');
});

// Create a new event listener that listens for any message that is not a command and tries to download media from the message text
bot.on('message', async (msg) => {
  // If the message contains a URL, try to download media from it
  if (msg.text && msg.text.match(/https?:\/\/(www\.)?instagram\.com\/p\/[a-zA-Z0-9_-]+/)) {
    try {
      // Download the media from the URL
      const result = await downloadMedia(msg.text);

      // Send the media to the user
      bot.sendDocument(msg.chat.id, result.data, { caption: `Here is the ${result.type} you requested.` });
    } catch (error) {
      // If there was an error, send an error message to the user
      bot.sendMessage(msg.chat.id, 'Sorry, I could not download the media from the provided URL.');
    }
  } else {
    // If the message does not contain a URL, send a message to the user asking for a valid URL
    bot.sendMessage(msg.chat.id, 'Please provide a valid Instagram post URL.');
  }
});
