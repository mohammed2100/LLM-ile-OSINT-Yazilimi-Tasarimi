import requests
from bs4 import BeautifulSoup

def get_tweets(name):
    base_url = "https://twitter.com/search"
    params = {
        'q': name,
        'src': 'typed_query',
        'f': 'live'
    }
    headers = {
        'User-Agent': 'Mozilla/5.0',
        'Accept': 'text/html,application/xhtml+xml'
    }

    try:
        response = requests.get(base_url, params=params, headers=headers)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            tweets = soup.find_all('article')
            
            results = []
            for tweet in tweets:
                text = tweet.find('div', {'data-testid': 'tweetText'})
                if text:
                    results.append({
                        'content': text.text.strip(),
                        'url': response.url
                    })
            return results
    except Exception as e:
        print(f"Hata: {e}")
    return []

if __name__ == "__main__":
    name = input("İsim girin: ")
    print("\nTweetler aranıyor...")
    
    tweets = get_tweets(name)
    if tweets:
        for tweet in tweets:
            print(f"\nTweet: {tweet['content']}")
            print(f"URL: {tweet['url']}")
            print("-" * 50)
    else:
        print("Tweet bulunamadı.")