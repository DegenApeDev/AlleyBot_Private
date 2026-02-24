import os
from typing import Dict
from plugin_manager import AlleyBotPlugin

class BrainXPostPlugin(AlleyBotPlugin):
    def __init__(self, config):
        super().__init__(config)
        self.name = "brain_x_post"
        self.version = "1.0.0"
        self.openai_client = None
        self.twitter_client = None
        try:
            import openai
            api_key = os.getenv('OPENAI_API_KEY')
            if api_key:
                self.openai_client = openai.OpenAI(api_key=api_key)
            else:
                print("Missing OPENAI_API_KEY")
        except Exception as e:
            print(f"OpenAI setup failed: {e}")
        try:
            import tweepy
            keys = {
                "consumer_key": os.getenv("TWITTER_API_KEY"),
                "consumer_secret": os.getenv("TWITTER_API_KEY_SECRET"),
                "access_token": os.getenv("TWITTER_ACCESS_TOKEN"),
                "access_token_secret": os.getenv("TWITTER_ACCESS_TOKEN_SECRET"),
            }
            if all(keys.values()):
                self.twitter_client = tweepy.Client(**keys)
            else:
                print("Missing Twitter API keys")
        except Exception as e:
            print(f"Tweepy setup failed: {e}")

    def get_commands(self) -> Dict[str, callable]:
        return {
            "brain_x_post": self.brain_x_post,
        }

    def brain_x_post(self, args: list) -> str:
        if not self.openai_client or not self.twitter_client:
            return "Plugin not ready. Set OPENAI_API_KEY and TWITTER_* env vars. Check logs."
        topic = " ".join(args).strip()
        if not topic:
            return "Usage: brain_x_post <crypto topic/content>"
        prompt = f"""Generate a viral crypto-degen style X/Twitter post or thread (3-5 tweets for complex topics) about: {topic}

Style: MAX HYPE, CAPSLOCK, emojis EVERYWHERE 🔥🚀💎🐂🦍 LFGGG🚀, alpha drops, create FOMO.
Include Solana on-chain embeds: e.g. https://solscan.io/token/EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v#sol or https://solscan.io/tx/exampletxhash
End EVERY tweet with CTA: "RT + Follow @DegenApeDev for more alpha 💯🙌"

If thread, separate tweets with '---'.
Pre-number in text like 1/4, 2/4 etc.
Keep EACH tweet <270 chars."""
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are @DegenApeDev, Solana degen shiller. Pump it hard."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.9,
                max_tokens=3000,
            )
            full_content = response.choices[0].message.content.strip()
        except Exception as e:
            print(f"LLM error: {e}")
            return f"LLM failed: {str(e)}"
        tweets = [t.strip() for t in full_content.split('---') if t.strip()]
        if not tweets:
            tweets = [full_content]
        tweets = [tweet[:277] + "..." if len(tweet) > 280 else tweet for tweet in tweets]
        posted_links = []
        prev_tweet_id = None
        try:
            for i, tweet_text in enumerate(tweets):
                if len(tweets) > 1:
                    tweet_text = f"{i+1}/{len(tweets)} {tweet_text}"
                if len(tweet_text) > 280:
                    tweet_text = tweet_text[:277] + "..."
                response = self.twitter_client.create_tweet(
                    text=tweet_text,
                    in_reply_to_tweet_id=prev_tweet_id
                )
                tweet_id = response.data["id"]
                posted_links.append(f"https://x.com/DegenApeDev/status/{tweet_id}")
                print(f"Posted tweet {i+1}/{len(tweets)}: {tweet_text[:60]}...")
                prev_tweet_id = tweet_id
            status = "thread" if len(tweets) > 1 else "post"
            return f"✅ {status.capitalize()} posted!\n" + "\n".join(posted_links)
        except Exception as e:
            print(f"Twitter post error: {e}")
            return f"❌ Post failed: {str(e)}"

PLUGIN_INFO = {
    "name": "brain_x_post",
    "version": "1.0.0",
    "description": "LLM-powered crypto degen X/Twitter threads/posts for @DegenApeDev with emojis, CTAs, Solscan embeds.",
    "author": "AlleyBot"
}

def create_plugin(config=None):
    return BrainXPostPlugin(config or {})