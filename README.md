Plan:
"Given origin destination an departure time what is the best route"
but how do i define best route?

- what route minimises expected delay and risk of disruption is a good idea 
Optimise for one of the following:
- fastest arrival
- lowest disruption risk
- fewest transfers
- or a balance 

start with a smaller area maybe sjust sydney trains 

output:
- top 3 route options
- estimated travel time 
- reliability score
- reason for recommendation 

main data sources to use 
- GTFS static timetable feed 
- GTFS realtime trip updates 
GTFS real time vehicle positions 


links being used:
https://opendata.transport.nsw.gov.au/data/dataset/public-transport-realtime-alerts-v2
https://opendata.transport.nsw.gov.au/data/dataset/public-transport-realtime-vehicle-positions-v2
https://opendata.transport.nsw.gov.au/dataset/historical-gtfs-and-gtfs-realtime
https://opendata.transport.nsw.gov.au/dataset/timetables-complete-gtfs