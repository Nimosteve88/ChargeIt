import pandas as pd
import xgboost as xgb
from sqlalchemy import create_engine, text

# Database connection details
DATABASE_URI = "postgresql+psycopg2://postgres:ChargeIt2024@chargeit-db-instance.cdflickwg4xn.us-east-1.rds.amazonaws.com:5432/initial_db"

# Setup SQLAlchemy
engine = create_engine(DATABASE_URI)

def fetch_historical_data():
    with engine.connect() as connection:
        result = connection.execute(text("""
            SELECT tick, buy_price, sell_price, day, timestamp
            FROM price_data
            ORDER BY tick ASC
        """))
        rows = [dict(row) for row in result]
    return rows

def prepare_features(data):
    df = pd.DataFrame(data, columns=['tick', 'buy_price', 'sell_price', 'day', 'timestamp'])
    #print("Initial DataFrame:\n", df)  # Debug statement
    
    df['price_diff'] = df['sell_price'] - df['buy_price']
    df['buy_ma'] = df['buy_price'].rolling(window=5).mean()
    df['sell_ma'] = df['sell_price'].rolling(window=5).mean()
    df.dropna(inplace=True)
    #print("DataFrame after feature preparation:\n", df)  # Debug statement
    
    return df

def train_model(df):
    X = df[['buy_price', 'sell_price', 'price_diff', 'buy_ma', 'sell_ma']]
    y = (df['sell_price'].shift(-1) > df['sell_price']).astype(int)  # Simplistic approach: 1 if price increases, else 0
    dtrain = xgb.DMatrix(X, label=y)
    param = {'max_depth': 3, 'eta': 0.1, 'objective': 'binary:logistic'}
    num_round = 100
    model = xgb.train(param, dtrain, num_round)
    return model, list(X.columns)

def test_model(model, df, feature_names):
    X = df[feature_names].iloc[-1].values.reshape(1, -1)
    dmatrix = xgb.DMatrix(X, feature_names=feature_names)
    prediction = model.predict(dmatrix)
    return prediction

def main():
    # Fetch historical data
    data = fetch_historical_data()
    if not data:
        print("No historical data found.")
        return

    # Prepare features
    df = prepare_features(data)
    
    # Train model
    model, feature_names = train_model(df)
    
    # Test model with the latest data point
    prediction = test_model(model, df, feature_names)
    
    print("Prediction for the next tick (1 = Buy, 0 = Sell):", prediction[0])

if __name__ == "__main__":
    main()
