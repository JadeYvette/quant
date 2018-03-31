from quantopian.pipeline import Pipeline
from quantopian.algorithm import attach_pipeline, pipeline_output
from quantopian.pipeline.data.builtin import USEquityPricing
from quantopian.pipeline.factors import SimpleMovingAverage
from quantopian.pipeline.factors import RSI
from quantopian.pipeline.factors import AverageDollarVolume
from quantopian.pipeline.factors import ExponentialWeightedMovingAverage
import numpy
from pandas import DataFrame
import pandas as pd
import talib
import datetime



def initialize(context):

    context.stock = sid(351)
    context.take_profit = .0233
    context.stop_loss = 0
    context.current_price = 0
    context.buy_price = 0
    context.cash = 0
    context.worth = 25000
    context.open_orders = 0
    context.price_hist_short = 0
    context.price_hist_long = 0
    context.mavg_short = 0 
    context.mavg_long = 0
    context.first_run = 0
    my_pipe = make_pipeline()
    attach_pipeline(my_pipe, 'my_pipeline')
    context.macd_raw = 0 
    context.signal = 0 
    context.macd_hist = []
    
    #for x in [0,1,2,3,4,5]:
    
        #schedule_function(rebalance, date_rules.every_day(), time_rules.market_open(hours=x, minutes=30))
   # set_max_order_count(4)
   

def make_pipeline():
    
    
     mean_close_10 = SimpleMovingAverage(
      inputs=[USEquityPricing.close],
      window_length=10
    )
        
     mean_close_30 = SimpleMovingAverage(
      inputs=[USEquityPricing.close],
      window_length=30
    )
    
     rsi_7 = RSI(
     inputs=[USEquityPricing.close],
     window_length=10
    )
   
     percent_difference = (mean_close_10 - mean_close_30) / mean_close_30
        
        
        
     rsi_under_35 = (rsi_7 < 35)

 
     latest_close = USEquityPricing.close.latest
     dollar_volume = AverageDollarVolume(window_length=30)
     high_dollar_volume = dollar_volume.percentile_between(85, 100)
    
    
     filters = high_dollar_volume & rsi_under_35
        
   
        
    
     return Pipeline(
    
         columns={
            
              '10_day_mean_close': mean_close_10,
              'latest_close_price': latest_close,
              'percent_difference':percent_difference,
              'dollar_value':dollar_volume
               
              
            },
         screen= filters
         
        )
        
def rebalance(context, data): 
    log.info("rebalance")  
    
def daily_checks(context,data):
    log.info("rebalance")  
   
    
def profit_sell(context,data):    
    
    if context.stock not in context.open_orders and context.portfolio.positions[context.stock.sid].amount > 0:
      if context.buy_price > 0: 
         sell_price = context.buy_price + (context.buy_price * context.take_profit)

         if sell_price <= context.current_price:
            number_of_shares = context.portfolio.positions[context.stock.sid].amount
            order(context.stock, -number_of_shares)
            log.info("profit_sell")  
  
        
    
def stop_sell(context,data):    
    
    if context.stock not in context.open_orders and context.portfolio.positions[context.stock.sid].amount > 0:
      if context.buy_price > 0: 
         stop_price = context.buy_price - (context.buy_price * .0233)
         if stop_price >= context.current_price:
            number_of_shares = context.portfolio.positions[context.stock.sid].amount
            order(context.stock, -number_of_shares)
            log.info("stop_sell")  
    
    
def MACD_sell(context,data):    
    
    if context.macd_hist[-1] < 0 and context.portfolio.positions[context.stock.sid].amount > 0 :
        if context.stock not in context.open_orders:
        # Before we sell we need to know how many shares we have
          number_of_shares = context.portfolio.positions[context.stock.sid].amount
          log.info("sold price")
          log.info(context.current_price)
          log.info(number_of_shares)
        # Now we can sell
          log.info("MACD_sell")
          order(context.stock, -number_of_shares) # When selling we need to pass a negative number of shares
            
              
def MACD_purchase(context,data):    
    
    if  context.macd_hist[-1] > 0 and context.cash > context.current_price and           context.portfolio.positions[context.stock.sid].amount > 0:
         if context.stock not in context.open_orders:
        # When buying we need to know how many shares we can buy
            number_of_shares = int(context.cash/context.current_price)
   
        # int() helps us get a integer value, we can't buy half a share you know
        
        # Finally, we place the buy order
           
            
            log.info( context.current_price)
 
            context.buy_price = context.current_price
            
        
       
            log.info("MACD_purchase") 
            log.info(context.stock)
            order(context.stock, number_of_shares)
            #order(stock, -number_of_shares, stop_price = current_price * 0.977) 

def before_trading_start(context, data):
  context.open_orders = get_open_orders() 
  if context.portfolio.positions[context.stock.sid].amount <= 0:
        result = pipeline_output('my_pipeline')
        result.sort_index(axis=0, level=1, ascending=True, inplace=True)
        result = result.sort_values(by=['percent_difference','dollar_value'], ascending=False)
        context.pipe_result = result.iloc[:1]
        update_universe(context.pipe_result) 
       # context.choosen_stock = false;
        
        for stock in context.pipe_result.index:
            context.stock = stock
            log.info(context.stock)
            log.info('changing stock') 
           # if context.stock != stock and context.choosen_stock == false:
           #    context.stock = stock
            #   context.choosen_stock = true;
            
           # elif context.stock == stock and context.choosen_stock == false:
            #     context.stock = stock
               #  context.choosen_stock = true;
                
            
            
                
def MACD_CALC(context,data):
  
    # Obtain price history in MINUTE interval
    #     Trim the 1-MINUTE interval data for 30-MINUTE intervals (Keep every 30 data points)
    #     Final data emulates Google Finance 1-Month window, 30-minute interval view
    price_history = data.history(
        context.stock,
        fields='price',
        bar_count=3000,
        frequency='1m')
    
    price_history = price_history[::30]
    context.macd_raw, context.signal, context.macd_hist = talib.MACD(price_history, 
                                             fastperiod=12, 
                                             slowperiod=26, 
                                             signalperiod=9)
    
            
        
def handle_data(context, data):
    # This handle_data function is where the real work is done.  Our data is
    # minute-level tick data, and each minute is called a frame.  This function
    # runs on each frame of the data.
    
    MACD_CALC(context,data)
        
   #Calculating MACD
    context.cash = context.portfolio.cash
    context.open_orders = get_open_orders()
    
   # if get_datetime().minute % 30 == 0 : 
    context.price_hist_short = data.history(context.stock, 'price',12, '1d')
    context.price_hist_long = data.history(context.stock, 'price',26, '1d')
        
 
    # And we will need Apple current and historic data

    # We will need average price data

    context.mavg_short = context.price_hist_short.mean()
    context.mavg_long =  context.price_hist_long.mean()
    
    # And the current price of the stock
    context.current_price = data.current(context.stock, 'price')
    

    # In order to make market decisions we need to know how much cash we have
    context.cash = context.portfolio.cash
    context.open_orders = get_open_orders()
    
    #running MACD ALGORITHM PIECES EVERY MINUTE
    
    MACD_purchase(context,data)
    MACD_sell(context,data)
  #  profit_sell(context,data)
    stop_sell(context,data)
