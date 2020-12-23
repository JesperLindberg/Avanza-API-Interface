# There will be two main sets of variables
class paths:
    BASE_URL =                   'https://www.avanza.se'
    SOCKET_URL =                 'wss://www.avanza.se/_push/cometd'
    POSITIONS_PATH =             BASE_URL + '/_mobile/account/positions'
    OVERVIEW_PATH =              BASE_URL + '/_mobile/account/overview'
    ACCOUNT_OVERVIEW_PATH =      BASE_URL + '/_mobile/account/{0}/overview'
    DEALS_AND_ORDERS_PATH =      BASE_URL + '/_mobile/account/dealsandorders'
    WATCHLISTS_PATH =            BASE_URL + '/_mobile/usercontent/watchlist'
    WATCHLISTS_ADD_DELETE_PATH = BASE_URL + '/_api/usercontent/watchlist/{0}/orderbooks/{1}'
    STOCK_PATH =                 BASE_URL + '/_mobile/market/stock/{0}'
    FUND_PATH =                  BASE_URL + '/_mobile/market/fund/{0}'
    CERTIFICATE_PATH =           BASE_URL + '/_mobile/market/certificate/{0}'
    INSTRUMENT_PATH =            BASE_URL + '/_mobile/market/{0}/{1}'
    ORDERBOOK_PATH =             BASE_URL + '/_mobile/order/{0}'
    ORDERBOOK_LIST_PATH =        BASE_URL + '/_mobile/market/orderbooklist/{0}'
    CHARTDATA_PATH =             BASE_URL + '/_mobile/chart/orderbook/{0}'
    ORDER_PLACE_DELETE_PATH =    BASE_URL + '/_api/order'
    ORDER_EDIT_PATH =            BASE_URL + '/_api/order/{0}/{1}'
    ORDER_GET_PATH =             BASE_URL + '/_mobile/order/{0}'
    SEARCH_PATH =                BASE_URL + '/_mobile/market/search/{0}'
    AUTHENTICATION_PATH =        BASE_URL + '/_api/authentication/sessions/usercredentials'
    TOTP_PATH =                  BASE_URL + '/_api/authentication/sessions/totp'
    INSPIRATION_LIST_PATH =      BASE_URL + '/_mobile/marketing/inspirationlist/{0}'
    TRANSACTIONS_PATH =          BASE_URL + '/_mobile/account/transactions/{0}'

class public:
    STOCK =               'stock'
    FUND =                'fund'
    BOND =                'bond'
    OPTION =              'option'
    FUTURE_FORWARD =      'future_forward'
    CERTIFICATE =         'certificate'
    WARRANT =             'warrant'
    ETF =                 'exchange_traded_fund'
    INDEX =               'index'
    PREMIUM_BOND =        'premium_bond'
    SUBSCRIPTION_OPTION = 'subscription_option'
    EQUITY_LINKED_BOND =  'equity_linked_bond'
    CONVERTIBLE =         'convertible'

    # Chartdata
    TODAY =         'TODAY'
    ONE_MONTH =     'ONE_MONTH'
    THREE_MONTHS =  'THREE_MONTHS'
    ONE_WEEK =      'ONE_WEEK'
    THIS_YEAR =     'THIS_YEAR'
    ONE_YEAR =      'ONE_YEAR'
    FIVE_YEARS =    'FIVE_YEARS'

    # Marketing
    HIGHEST_RATED_FUNDS =                       'HIGHEST_RATED_FUNDS'
    LOWEST_FEE_INDEX_FUNDS =                    'LOWEST_FEE_INDEX_FUNDS'
    BEST_DEVELOPMENT_FUNDS_LAST_THREE_MONTHS =  'BEST_DEVELOPMENT_FUNDS_LAST_THREE_MONTHS'
    MOST_OWNED_FUNDS =                          'MOST_OWNED_FUNDS'

    # Transactions
    OPTIONS =          'options'
    FOREX =            'forex'
    DEPOSIT_WITHDRAW = 'deposit-withdraw'
    BUY_SELL =         'buy-sell'
    DIVIDEND =         'dividend'
    INTEREST =         'interest'
    FOREIGN_TAX =      'foreign-tax'

    # Channels
    ACCOUNTS =           'accounts'
    QUOTES =             'quotes'
    ORDERDEPTHS =        'orderdepths'
    TRADES =             'trades'
    BROKERTRADESUMMARY = 'brokertradesummary'
    POSITIONS =          'positions'
    ORDERS =             'orders'
    DEALS =              'deals'

    # Order types
    BUY =  'BUY'
    SELL = 'SELL'

    # Variables used
    MIN_INACTIVE_MINUTES = 30
    MAX_INACTIVE_MINUTES = 60 * 24
    MAX_BACKOFF_MS =       2 * 60 * 1000
    USER_AGENT =           'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36'