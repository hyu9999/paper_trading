import pandas as pd
from pytdx.hq import TdxHq_API

from paper_trading.utility.setting import SETTINGS

# 市场代码对照表
exchange_map = {}
exchange_map["SH"] = 1
exchange_map["SZ"] = 0


class PYTDXService:
    """pytdx数据服务类"""

    def __init__(self, client):
        """Constructor"""
        self.connected = False  # 数据服务连接状态
        self.hq_api = None  # 行情API
        self.client = client  # mongo client

    def connect_api(self):
        """连接API"""
        # 连接增强行情API并检查连接情况
        try:
            if not self.connected:
                host = SETTINGS["TDX_HOST"]
                port = SETTINGS["TDX_PORT"]
                self.hq_api = TdxHq_API()
                self.hq_api.connect(host, port)
                self.connected = True
            return True
        except Exception:
            raise ConnectionError("pytdx连接错误")

    def get_realtime_data(self, symbol: str):
        """获取股票实时数据"""
        try:
            symbols = self.generate_symbols(symbol)
            df = self.hq_api.to_df(self.hq_api.get_security_quotes(symbols))
            data = self.client["stocks"]["security"].find_one(
                {"code": symbols[0][1], "market": str(symbols[0][0])}
            )
            # 处理基金价格：通达信基金数据是实际价格的10倍
            if data["decimal_point"] == 3:
                df["price"] = df["price"] / 10
                df["last_close"] = df["last_close"] / 10
                df["open"] = df["open"] / 10
                df["high"] = df["high"] / 10
                df["low"] = df["low"] / 10
                df["ask1"] = df["ask1"] / 10
                df["bid1"] = df["bid1"] / 10
                df["ask2"] = df["ask2"] / 10
                df["bid2"] = df["bid2"] / 10
                df["ask3"] = df["ask3"] / 10
                df["bid3"] = df["bid3"] / 10
                df["ask4"] = df["ask4"] / 10
                df["bid4"] = df["bid4"] / 10
                df["ask5"] = df["ask5"] / 10
                df["bid5"] = df["bid5"] / 10
            return df
        except Exception:
            raise ValueError("股票数据获取失败")

    def get_history_transaction_data(self, symbol, date):
        """
        查询历史分笔数据
        get_history_transaction_data(TDXParams.MARKET_SZ, '000001', 0, 10, 20170209)
        参数：市场代码, 股票代码, 起始位置, 数量, 日期
        输出[time, price, vol, buyorsell(0:buy, 1:sell, 2:平)]
        """
        # 获得标的
        code, market = self.check_symbol(symbol)

        # 设置参数
        check_date = int(date)
        count = 2000
        data_list = []
        position = [6000, 4000, 2000, 0]
        for start in position:
            data = self.hq_api.to_df(
                self.hq_api.get_history_transaction_data(
                    market, code, start, count, check_date
                )
            )
            data_list.append(data)

        df = pd.concat(data_list)
        df.drop_duplicates(inplace=True)
        return df

    @staticmethod
    def generate_symbols(symbol: str):
        """组装symbols数据，pytdx接收的是以市场代码和标的代码组成的元祖的list"""
        new_symbols = []
        code, exchange = symbol.split(".")
        new_symbols.append((exchange_map[exchange], code))

        return new_symbols

    @staticmethod
    def check_symbol(symbol: str):
        """检查标的格式"""
        if symbol:
            code, market = symbol.split(".")
            market = exchange_map.get(market)
            return code, market

        else:
            return False

    def close(self):
        """数据服务关闭"""
        self.connected = False
        self.hq_api.disconnect()
