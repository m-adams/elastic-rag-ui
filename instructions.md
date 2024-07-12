## Welcome to the Elasticsearch ReMapper!

This is a simple App to walk through the steps of adjusting an existing mapping of an index by reindexing in to a new index with an updated mapping. It also facilitates best practice to use index aliases to refer to indexes and also allows you to reindex through a pipeline to modify the data.

### Steps
1. Enter your connection details in the sidebar. These can also be set through ENV variables or in an .env file
2. Select the index you want to remap. You can search using a pattern
4. Click the "Select Index" button
5. (Optional) If you want to move an alias associated with the index select it in the dropdown
6. (Optional) If you want to use an index pipeline to process the data, search for the pipeline, select and make sure to test the pipeline
7. Adjust the mapping and click save
8. Click the "Remap" button
9. You can see progress in the "Status Updates" section
