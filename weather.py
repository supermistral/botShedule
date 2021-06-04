import requests, settings


class Weather:
    def __init__(self):
        self.url = "http://api.openweathermap.org/data/2.5/"
        self.url_weather_now = self.url + "weather"
        self.url_weather_forecast = self.url + "forecast"
        self.windDirections = [
            "северный", "северно-восточный", "восточный", "юго-восточный", "южный",
            "юго-западный", "западный", "северо-западный"
        ]
        self.params = {
            'q': 'moscow', 
            'appid': settings.TOKEN_WEATHER,
            'units': 'metric',
            'lang': 'ru'  
        }

    
    def get_weaher_response(self, url: str) -> dict or None:
        response = requests.get(url, params=self.params)
        if response.status_code != 200:
            return None
        return response.json()

    
    def get_weather_now(self) -> str:
        json = self.get_weaher_response(self.url_weather_now)

        if json is None:
            return "Произошла ошибка связи с сервисом погоды"

        return self.parse_weather_response(json)


    def get_weather_today(self) -> str:
        json = self.get_weaher_response(self.url_weather_forecast)
        json = [json["list"][x] for x in range(1, 8, 2)]    # 6:00 12:00 18:00 00:00 - утро день вечер ночь

        if json is None:
            return "Произошла ошибка связи с сервисом погоды"

        dayUnits = ["УТРО", "ДЕНЬ", "ВЕЧЕР", "НОЧЬ"]
        stringWeather = ""

        for ind in range(len(dayUnits)):
            stringWeather += dayUnits[ind] + "\n"
            stringWeather += self.parse_weather_response(json[ind], " / / ") + "\n"

        return stringWeather

    
    def parse_weather_response(self, weather: dict, firstSyms: str = "") -> str:
        description             = weather["weather"][0]["description"]
        temperature             = f'{int(weather["main"]["temp_min"])} - {int(weather["main"]["temp_max"])}℃'
        pressure                = int(weather["main"]["pressure"] * 100 * 760 / 101325)
        humidity                = weather["main"]["humidity"]
        windSpeed               = int(weather["wind"]["speed"])
        windIndexInDirections   = int(((weather["wind"]["deg"] + 22.5) % 360) // 45)

        stringWeather = f"{firstSyms}{description[0].upper() + description[1:]}, температура: {temperature}\n" + \
            f"{firstSyms}Давление: {pressure} мм рт.ст., влажность: {humidity}%\n" + \
            f"{firstSyms}Ветер: {windSpeed} м/с, {self.windDirections[windIndexInDirections]}"

        return stringWeather



if __name__ == "__main__":
    weather = Weather()
    print(weather.get_weather_today())