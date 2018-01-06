package main_body;

import pre_processing.WordSeg;
import wildcard_search.WildCardSearch;

public class BodyMethod {
	
	
	/**
	 * @param query			用户输入的查询串	
	 * @param searchType	1为普通检索，2为通配符检索
	 * @return
	 */
	public static String[] getSearchResult(String query, int searchType){
		
//		String[] queryWords = WordSeg.segmentation(query);
		
		String[] result = null;
		if(searchType == 1){
			
		}
		
		if(searchType == 2){
//			result = WildCardSearch.getWCSresults(query);
		}
		
		return result;
	}
}
