# Project documentation

## Data Selection

In our initial brainstorming, the most prominent ideas for the project were modelling each countries performance against their given odds in previous soccer World cups or to model the effects of weather on shipping routes. We agreed that we were more likely to get available data from the second option, so we started looking for data on global shipping to match with widely available weather data. However, the scope was revealed to be too broad, and we had trouble on getting shipping data that would allow us to pinpoint some kind of delays or disruptions. This prompted us to narrow the scope down to checking the effects of weather on a more local level and we decided to focus on single city’s public transport instead of shipping. We were able to find suitable data on disruptions in train traffic from the Netherlands, so we decided to model the effects of weather on the Amsterdam Central train delays. 

The selected data sources were an independent website “Rijden de Treinen” for train disruptions and open-meteo.com.

## Extraction

The data is accessed with Python scripts whcich download it locally. At this stage the data is kept on a one file per year per data source level to avoid possible issues with file size.

While deciding the data granularity, we discussed wether we would have the smallest grain be disruptions & weather by the day or by the hour. We decided to have the granularity be by the hour, since it would give us more accurate information about the correlation between weather and disruptions. Additinally, while doing the report we could aggregate from by the hour to by the day format, but not the other way around.

## Transformation

## Medallion Architechture

### Bronze
The freshly downloaded raw files are stored locally in CSV format

### Silver
Data is cleaned with python by removing excess columns and standardizing the formatting for dates etc. After this the cleaned & standardized data is uploaded to a shared sql database.

### Gold
In the database, data is organised into tables that can be used in the data warehouse. Finally the warehouse is being used in a Power BI report. 

