This folder contains 
1. Lucene vs BM25:
		This PDF contains the table comparing the number of documents retrieved by Lucene
		and BM25 algorithm for each query.
2. Folder "Query Output":
		This folder contains the a text file for each query. Each text file contains top 100 
		documents and their score calculated using Lucene.
3. HW4.java:
		This file is the source code for indexing and retrieval of top 100 documents ranked using
		Lucene library.
4. SortedListOfTermFreqPair.txt:
		This text file contains sorted(by frequency) list of (term, term_freq pairs) done using SimpleAnalyzer
		of Lucene library, only words pre and html are ignored.
5. Zipf.png:
		This png file plots the occurence and rank of the term in the whole collection.
		
The program:
	The program runs using the three libraries mentioned on the assignment page. The output of the program
	is two text files. The the top 100 documents for a query and pair (term,term-frequency), the program runs 
	once for every query in sorted order. The program terminates after one query. To run for the next query 
	delete all the files from the current output folder.
	
	To run: (after setting up the Lucene libraries)
		javac HW4.java
		java HW4
		
		Enter when asked by the program: 1. Provide the folder where index files has to created
										 2. Provide the corpus file or the directory address where the corpuses are present
										 3. When prompoted, enter the query to be searched for. 
										 4. The output is generated.
		