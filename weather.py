import requests, settings


class Weather:
    def __init__(self):
        self.url = "http://api.openweathermap.org/data/2.5/weather"
        self.params = {
            'q': 'moscow', 
            'appid': settings.TOKEN_WEATHER,
            'units': 'metric',
            'lang': 'ru'  
        }

    
    def get_weather(self):
        response = requests.get(self.url, params=self.params)

        print(response.json())



if __name__ == "__main__":
    weather = Weather()
    weather.get_weather()