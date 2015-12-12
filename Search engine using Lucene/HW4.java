import java.io.BufferedReader;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileReader;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.PrintWriter;
import java.io.Reader;
import java.io.StringReader;
import java.io.StringWriter;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashMap;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Map.Entry;
import java.util.Set;
import java.util.stream.Collectors;

import org.apache.lucene.analysis.Analyzer;
import org.apache.lucene.analysis.TokenStream;
import org.apache.lucene.analysis.Tokenizer;
import org.apache.lucene.analysis.charfilter.HTMLStripCharFilter;
import org.apache.lucene.analysis.compound.hyphenation.TernaryTree.Iterator;
import org.apache.lucene.analysis.core.SimpleAnalyzer;
import org.apache.lucene.analysis.standard.StandardAnalyzer;
import org.apache.lucene.analysis.tokenattributes.CharTermAttribute;
import org.apache.lucene.analysis.tokenattributes.OffsetAttribute;
import org.apache.lucene.document.Document;
import org.apache.lucene.document.Field;
import org.apache.lucene.document.StringField;
import org.apache.lucene.document.TextField;
import org.apache.lucene.index.DirectoryReader;
import org.apache.lucene.index.DocsEnum;
import org.apache.lucene.index.Fields;
import org.apache.lucene.index.IndexReader;
import org.apache.lucene.index.IndexWriter;
import org.apache.lucene.index.IndexWriterConfig;
import org.apache.lucene.index.IndexableField;
import org.apache.lucene.index.MultiFields;
import org.apache.lucene.index.Term;
import org.apache.lucene.index.Terms;
import org.apache.lucene.index.TermsEnum;
import org.apache.lucene.queryparser.classic.QueryParser;
import org.apache.lucene.search.DocIdSetIterator;
import org.apache.lucene.search.IndexSearcher;
import org.apache.lucene.search.Query;
import org.apache.lucene.search.ScoreDoc;
import org.apache.lucene.search.TopScoreDocCollector;
import org.apache.lucene.store.FSDirectory;
import org.apache.lucene.util.Bits;
import org.apache.lucene.util.BytesRef;
import org.apache.lucene.util.IOUtils;
import org.apache.lucene.util.Version;

/**
 * To create Apache Lucene index in a folder and add files into this index based
 * on the input of the user.
 */
public class HW4 {
    private static Analyzer Analyzer = new SimpleAnalyzer(Version.LUCENE_47);

    private IndexWriter writer;
    private ArrayList<File> queue = new ArrayList<File>();
    static PrintWriter pwr, printwr, printAllText, printQueryOutput, printFrequency ;
    static HashMap<String,Integer> termFrequency = new HashMap<>();
    static HashSet<Integer> docId = new HashSet<>();
    static int docCount = 0;
    public static void main(String[] args) throws IOException {
	System.out
		.println("Enter the FULL path where the index will be created: (e.g. /Usr/index or c:\\temp\\index)");

	String indexLocation = null;
	BufferedReader br = new BufferedReader(new InputStreamReader(System.in));
	String s = br.readLine();

	HW4 indexer = null;
	try {
		pwr = new PrintWriter("Tokens.txt","UTF-8");
		printwr = new PrintWriter("HashMap.txt","UTF-8");
		printAllText = new PrintWriter("AllText.txt","UTF-8");
		printFrequency = new PrintWriter("AllFrequencyForZipf.txt","UTF-8");
	    indexLocation = s;
	    indexer = new HW4(s);
	} catch (Exception ex) {
	    System.out.println("Cannot create index..." + ex.getMessage());
	    System.exit(-1);
	}

	// ===================================================
	// read input from user until he enters q for quit
	// ===================================================
	//while (!s.equalsIgnoreCase("q")) {
	    try {
		System.out
			.println("Enter the FULL path to add into the index (q=quit): (e.g. /home/mydir/docs or c:\\Users\\mydir\\docs)");
		System.out
			.println("[Acceptable file types: .xml, .html, .html, .txt]");
		s = br.readLine();
		//if (s.equalsIgnoreCase("q")) {
		//    break; //Exists the while loop and closes the 
		//}

		// try to add file into the index
		indexer.indexFileOrDirectory(s);
	    } catch (Exception e) {
		System.out.println("Error indexing " + s + " : "
			+ e.getMessage());
	    }
	//}
	
	// ===================================================
	// after adding, we always have to call the
	// closeIndex, otherwise the index is not created
	// ===================================================
	indexer.closeIndex();

	// =========================================================
	// Now search
	// =========================================================
	IndexReader reader = DirectoryReader.open(FSDirectory.open(new File(
		indexLocation)));
	IndexSearcher searcher = new IndexSearcher(reader);
	TopScoreDocCollector collector = TopScoreDocCollector.create(100, true);
	
		// =========================================================
		// //Calculates the frequency of every word.
		// =========================================================
	int count = 1;
	Double totalFrequency = 0.0;
	while(count < docCount){
		/*
		printAllText.println(reader.document(count).getField("contents"));
		printAllText.println("=================================");
		printAllText.flush();
		*/
		IndexableField tokenizedComponentField = reader.document(count).getField("contents");
		TokenStream tr = tokenizedComponentField.tokenStream(Analyzer);
		OffsetAttribute offsetAtt = tr.addAttribute(OffsetAttribute.class);
        CharTermAttribute charTermAttribute = tr.addAttribute(CharTermAttribute.class);
		tr.reset();
		while(tr.incrementToken()){
			String term = charTermAttribute.toString();
			if(!term.equals("html") && !term.equals("pre")){
				if(termFrequency.get(term) != null){
					termFrequency.put(term, termFrequency.get(term) + 1 );
					totalFrequency++;
				}
				else{
					termFrequency.put(term, 1 );
					totalFrequency++;
				}
			}
		}
		tr.close();
		count++;
	}
	//printAllText.close();
	
	//Sorts the list of frequency using lambda and stream functions of java
	LinkedHashMap sortedFreq = termFrequency.entrySet().stream()
			.sorted(Map.Entry.comparingByValue(Comparator.reverseOrder()))
			.collect(Collectors.toMap(
					Map.Entry::getKey, 
					Map.Entry::getValue, 
					(x,y)-> {throw new AssertionError();},
					LinkedHashMap::new
					));

	//Prints the frequency and the term frequency pair
	java.util.Iterator sortedFreqIterator = sortedFreq.entrySet().iterator();
	while(sortedFreqIterator.hasNext()){
		Map.Entry mentry = (Map.Entry)sortedFreqIterator.next();
		printwr.println(mentry.getKey()+" "+mentry.getValue());
		printwr.flush();
		//printFrequency.println(""+(((int)mentry.getValue()/totalFrequency)*100));
		//printFrequency.flush();
		}
	printwr.close();
	//printFrequency.close();
    
			// =========================================================
			// //Ending of Calculating the frequency of every word.
			// =========================================================
	
	s = "";
	//while (!s.equalsIgnoreCase("q")) {
	    try {
		System.out.println("Enter the search query (q=quit):");
		s = br.readLine();
		printQueryOutput = new PrintWriter("Query-"+s+"-output.txt","UTF-8");
		//if (s.equalsIgnoreCase("q")) {
		//    break;
		//}
		

		Query q = new QueryParser(Version.LUCENE_47, "contents",
			Analyzer).parse(s);
		searcher.search(q, collector);	
		ScoreDoc[] hits = collector.topDocs().scoreDocs;
		// 4. display results
		System.out.println("Found " + hits.length + " hits.");
		for (int i = 0; i < hits.length; ++i) {
		    int docId = hits[i].doc;
		    Document d = searcher.doc(docId);
		    System.out.println((i + 1) + ". " + d.get("path")
			    + " score=" + hits[i].score);
		    printQueryOutput.println((i + 1) +" "+ (docId+1) +" "+ hits[i].score);
		    printQueryOutput.flush();
		    //printFrequency.println(docId+1);
		  	//printFrequency.flush();
		}
		printQueryOutput.close();
		System.out.println("Please check the output files and delete the index from the folder before next run");
	    } catch (Exception e) {
		System.out.println("Error searching " + s + " : "
			+ e.getMessage());
		//break;
	    }

	}

    //}

    /**
     * Constructor
     * 
     * @param indexDir
     *            the name of the folder in which the index should be created
     * @throws java.io.IOException
     *             when exception creating index.
     */
    HW4(String indexDir) throws IOException {    	
	FSDirectory dir = FSDirectory.open(new File(indexDir));
	IndexWriterConfig config = new IndexWriterConfig(Version.LUCENE_47,
		Analyzer);

	writer = new IndexWriter(dir, config);
    }

    /**
     * Indexes a file or directory
     * 
     * @param fileName
     *            the name of a text file or a folder we wish to add to the
     *            index
     * @throws java.io.IOException
     *             when exception
     */
    @SuppressWarnings("deprecation")
	public void indexFileOrDirectory(String fileName) throws IOException {
	// ===================================================
	// gets the list of files in a folder (if user has submitted
	// the name of a folder) or gets a single file name (is user
	// has submitted only the file name)
	// ===================================================
	addFiles(new File(fileName));
	
	int originalNumDocs = writer.numDocs();
	for (File f : queue) {
	    FileReader fr = null;
	    //
	    HTMLStripCharFilter charFilter = null;
	    //
	    try {
		Document doc = new Document();

		// ===================================================
		// add contents of file
		// ===================================================
		fr = new FileReader(f);
		//My added code
		String contents = new String(Files.readAllBytes(Paths.get(f.getPath())), StandardCharsets.UTF_8);
 		doc.add(new TextField("contents", contents, Field.Store.YES));
		doc.add(new StringField("path", f.getPath(), Field.Store.YES));
		doc.add(new StringField("filename", f.getName(), Field.Store.YES));
		writer.addDocument(doc);
		System.out.println("Added: " + f);
	    } catch (Exception e) {
		System.out.println("Could not add: " + f);
	    } finally {
		fr.close();
	    }
	}

	int newNumDocs = writer.numDocs();
	System.out.println("");
	System.out.println("************************");
	System.out
		.println((newNumDocs - originalNumDocs) + " documents added.");
	System.out.println("************************");
	docCount = newNumDocs - originalNumDocs;

	queue.clear();
    }

    private void addFiles(File file) {

	if (!file.exists()) {
	    System.out.println(file + " does not exist.");
	}
	if (file.isDirectory()) {
	    for (File f : file.listFiles()) {
		addFiles(f);
	    }
	} else {
	    String filename = file.getName().toLowerCase();
	    // ===================================================
	    // Only index text files
	    // ===================================================
	    if (filename.endsWith(".htm") || filename.endsWith(".html")
		    || filename.endsWith(".xml") || filename.endsWith(".txt")) {
		queue.add(file);
	    } else {
		System.out.println("Skipped " + filename);
	    }
	}
    }

    /**
     * Close the index.
     * 
     * @throws java.io.IOException
     *             when exception closing
     */
    public void closeIndex() throws IOException {
	writer.close();
    }
}