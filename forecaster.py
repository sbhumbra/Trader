class Forecaster:
    def __init__(self, haven_coin):
        self.haven_coin = haven_coin

    def forecast(self, coin, timestamp):
        # timestamp or vector of timestamps
        pass

    def validate(self, coin, timestamps):
        # call with past timestamps to verify algorithm goodness
        pass
