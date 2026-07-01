# Description of the data

When you use this dataset, it is important to realize that this data is about disruptions which have been communicated by NS. Not every train that is delayed or cancelled is communicated by NS as a disruption; the rule of thumb that NS uses is that a disruption is communicated when multiple trains are delayed or cancelled (i.e. a major impact of the train service).

It is also important to realize that since 2017, more disruptions have been communicated, because NS introduced a new system which allowed them to announce disruptions more timely (which resulted in more disruptions with a short duration). Comparing the number of disruptions from 2017 with the number of disruptions in the years before is therefore not possible (unless you account for the increase in short disruptions).

The source for the disruptions is always NS; the department for travel information at NS monitors the train service 24 hours a day to see if there are any disruptions. The disruption messages in the open data are the same as the messages on the boards at the station, the station PA and on the Rijden de Treinen website and app.

# Columns
This dataset contains the following columns:

### rdt_id Unique identifier
This is the ID that Rijden de Treinen uses for a disruption. When you open a disruption in the disruption archive, you can find the ID in the URL of the disruption page. For example, the ID for this disruption between Amsterdam Zuid and Schiphol is 12345.

### ns_lines Affected lines (from disruption message)
These are the lines linked to a disruption by NS. For the disruption in the example, this is Schiphol-Almere C./Hilversum/Utrecht C.
Attention:
A problem with the lines in this column (when you want to analyze the data) is that they are not standardized. This column is therefore less suitable for analysis. Use the rdt_lines column instead.

### rdt_lines Affected lines (linked by Rijden de Treinen)
These are the lines linked to a disruption by Rijden de Treinen. This is always based on the list of lines of Rijden de Treinen, and the link is based on the stations where a disruption is located.

In the example, the disruption is between Amsterdam Zuid and Schiphol. Rijden de Treinen then links the lines Amersfoort-Schiphol, Lelystad-Schiphol and Utrecht-Schiphol. The lines are always linked in alphabetical order, separated by a comma.

### rdt_lines_id Line IDs of affected lines
These are the IDs of the lines linked to a disruption by Rijden de Treinen, separated by a comma.

### rdt_station_names Affected stations (linked by Rijden de Treinen)
Based on the link with the lines, Rijden de Treinen also calculates which stations are affected by a disruption. In this column you can find the station names of the affected stations, separated by a comma.

### rdt_station_codes Station codes of affected stations
These are the codes (abbreviations) of the affected stations, separated by a comma. The station codes can be found in the dataset with railway stations.

### cause_nl Disruption cause (in Dutch)
This is the cause of a disruption, in Dutch. When the cause of a disruption is changed by NS during a disruption, the last used cause is shown in this column.

### cause_en Disruption cause (in English)
The disruption cause translated into English.

### statistical_cause_nl Statistical disruption cause (in Dutch)
For statistical purposes, Rijden de Treinen also keeps track of a statistical cause. When the cause of a disruptions is changed, information about the actual cause of a disruption is sometimes lost.

For example, sometimes a disruption cause is changed to the generic an earlier disruption or repair works. When a more descriptive disruption cause is available, this cause is stored as the statistical cause.

### statistical_cause_en Statistical disruption cause (in English)
The statistical disruption cause, but then translated into English.

### cause_group Disruption cause group
The group in which the disruption is classified (in English). You can find the groups in the list with disruption causes.

### start_time Start time
The time when the disruption started.

### end_time End time
The time when the disruption ended.

### duration_minutes Duration (in minutes)
The duration of the disruption in minutes.
