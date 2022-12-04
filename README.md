Given the following scenario: 

You aim to merge many records through an API call
Each record has 100 fields
You can call the API with any number of fields for each record (e.g., just one, or all 100)
The API call fails without any explanation if any of the fields is invalid
You are not at the outset sure what % of fields is invalid
For this simulation we are not trying to learn which fields are usually the invalid ones (though that would usually be a good idea IRL)

Goal: model several strategies for updating all valid fields with the minimum number of API calls

Strategies tested:
- Run each field, one-by-one (which of course yields 1 API call per field)
- A "naive binary" model  sends half the records to the API with each call, then drills down recursively on failed API calls, successively splitting the remaining records in half
- A "smart binary" model first partitions each record into a number of fields such that each API call has approximately a 50/50 chance of succeeding. When a call fails, the "naive binary" model is used to drill down recursivily on the remaining records (i.e., we split the failed list of fields in half, and run each of them, continuing recursively until all valid fields have been processed)

![Results](sim_chart.png)
