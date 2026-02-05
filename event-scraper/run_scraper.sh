export MONGO_URI=${MONGO_URI:-mongodb://localhost:27017}
export MONGO_DB=${MONGO_DB:-events_db}
python -m scraper.main
