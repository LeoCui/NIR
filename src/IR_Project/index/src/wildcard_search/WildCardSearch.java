package wildcard_search;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.Map.Entry;

public class WildCardSearch {
	
	/**
	 * @param docs 内含两个 ArrayList ，第0个 ArrayList 表示获取的倒排记录表中的词项集
	 * 						      第1个 ArrayList 与第0个 ArrayList 一一对应，表示词项集中一一对应的词项 hash 值
	 * @return 每个ArrayList中的元素是一个ArrayList（分别包含2-gram 拆解项<String类型>，该项对应的所有term_id<Arraylist类型>）
	 */
	public static ArrayList<ArrayList<Object>> buildWCSIT(ArrayList<ArrayList<Object>> docs){
		
		ArrayList<Object> terms = docs.get(1);
		ArrayList<Object> term_id = docs.get(0);
		
		return get2gramWords(term_id, terms);
	}
	
//	public static String[] getWCSresults(String query){
//		
//		String[] two_gram_qw = get2gramWords(query);
//		
//		//根据检索词的2-gram字对查找DB
//		// add by qtw
//		return two_gram_qw;
//	}
	
	/**
	 * @param term_id 词项集对应的hash集
	 * @param terms 词项集
	 * @return 每个arraylist中的元素是一个arraylist（分别包含2-gram 拆解项<String类型>，该项对应的所有term_id<Arraylist类型>）
	 */
	public static ArrayList<ArrayList<Object>> get2gramWords(ArrayList<Object> term_id, ArrayList<Object> terms){
		
		HashMap<String, ArrayList<Object>> two_gram_termIds = new HashMap<>();
		
		// 遍历词典(dictionary表)中所有词
		for(int i = 0; i < term_id.size(); i++){
			Object id = term_id.get(i);
			String term = (String) terms.get(i);
			
			// 将term进行2gram拆解
			String[] two_gram_subseq = get2gram_subseq(term);
			for(int j = 0; j < two_gram_subseq.length; j++){
				String tg_subseq = two_gram_subseq[j];
				
				// 防止返回的2gram拆解为空，便于测试
				if(tg_subseq == null){
					System.out.println( "2 gram of " + term + " is null");
				}
				
				if(two_gram_termIds.containsKey(tg_subseq)){
					ArrayList<Object> ids = two_gram_termIds.get(tg_subseq);
					ids.add(id);
					two_gram_termIds.put(tg_subseq, ids);
				}else{
					ArrayList<Object> ids = new ArrayList<>();
					ids.add(id);
					two_gram_termIds.put(tg_subseq, ids);
				}
			}
		}

		// 组装返回的结果，内含的每个ArrayList包含两列
		// 第一列是2-gram 拆解项<String类型>
		// 第二列是该项对应的所有term_id<Arraylist类型>
		ArrayList<ArrayList<Object>> result = new ArrayList<>();
		
		for( Entry<String,ArrayList<Object>> entry : two_gram_termIds.entrySet() ){	
			
//			String tg_subseq = (String) entry.getKey();
//			ArrayList<Object> ids = (ArrayList<Object>) entry.getValue();
			
			ArrayList<Object> res = new ArrayList<>();
			res.add(entry.getKey());
			res.add(entry.getValue());

			result.add(res);
		}
		
		return result;
	}
	
	/**
	 * @param term 倒排记录表中的词项
	 * @return  对该词项进行2-gram切分后的 string 数组
	 */
	public static String[] get2gram_subseq(String term){
		
		String[] two_gram_WordPart = new String[term.length() + 1];
		two_gram_WordPart[0] = "$" + term.substring(0, 1);
		
		// 便于调试，以查看2-gram分词结果是否正确
//		StringBuilder stringBuilder = new StringBuilder(two_gram_WordPart[0] + " ");
		
		for(int j = 0; j < term.length() - 1; j++){
			two_gram_WordPart[j+1] = term.substring(j, j+2);
//			stringBuilder.append(two_gram_WordPart[j+1] + " ");
		}
		two_gram_WordPart[term.length()] = term.substring(term.length()-1, term.length()) + "$";
//		stringBuilder.append(two_gram_WordPart[term.length()]);
		
//		System.out.println(term + ": " + stringBuilder.toString());
		
		return two_gram_WordPart;
	}

}
