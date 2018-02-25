package db;

import java.util.ArrayList;
import java.util.Collection;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Map.Entry;
import java.util.zip.CRC32;

import dictionary.dictionarySystem;
import wildcard_search.WildCardSearch;

public class utils {
	
	/**
	 * @param content_not_handled 待拼接成完整文档内容的ArrayList<片段>
	 * @return 将每个分段中的内容拼接，返回完整的每篇文章的内容
	 */ 
	public String getDocByContentSequence(ArrayList<Object> content_not_handled){
		
		StringBuilder doc = new StringBuilder();
		
		for(int i=0; i<content_not_handled.size(); i++){
			doc.append(content_not_handled.get(i));
		}
		
		return doc.toString();
	}

	/**
	 * @param arlList 带重的words分词结果
	 * @return 去重的words list
	 */
	public ArrayList<String> removeWordsDuplicate(ArrayList<String> arlList) {
		HashSet<String> h = new HashSet<String>(arlList);      
		arlList.clear();      
		arlList.addAll(h);
		return arlList;
	}
	
	/**
	 * @param term 待计算hash值的词项
	 * @return 该词项对应的hash值（使用crc32来计算）
	 */
	public long getTermHash(String term) {
		
		CRC32 crc32 = new CRC32();
		crc32.update(term.getBytes());
		
		return crc32.getValue();
	}

	/**
	 * @param db_ip 数据库连接所需的ip地址
	 * @param db_port 数据库连接所需的port端口号
	 * @param db_name 数据库连接所需的用户名
	 * @param db_pwd 数据库连接所需的密码
	 * @param db_dictionary 需要操作的相关dictionary表名
	 * @param db_kgramIndex 需要操作的相关kgramIndex表名
	 * @param dictionaeyNotHandled 尚未进行k-gram处理的词项
	 * 作用：具体处理 k-gram表 + dictionary表(该表的存在是为了便于k-gram的存在)
	 */
	@SuppressWarnings("unchecked")
	public void handleKGram(String db_ip, int db_port, String db_name, String db_pwd, 
							String db_dictionary, String db_kgramIndex,
							ArrayList<ArrayList<Object>> dictionaeyNotHandled) {

		// 1.1.将k-gram结果去重,便于后续建立k-gram表
		ArrayList<ArrayList<Object>> k_gram_List = WildCardSearch.buildWCSIT(dictionaeyNotHandled);
		System.out.println("2-gram分解成功");
		HashMap<String, ArrayList<Object>> k_gram_map = new HashMap<>();
		
		for ( ArrayList<Object> item : k_gram_List ){
			
			if(!k_gram_map.containsKey(item.get(0))){
				k_gram_map.put((String) item.get(0), (ArrayList<Object>) item.get(1));
			}else {
				ArrayList<Object> tempLocal = k_gram_map.get(item.get(0));
				tempLocal.addAll((Collection<? extends Object>) item.get(1));
				k_gram_map.replace((String) item.get(0), tempLocal);
			}
		}
		
		ArrayList<ArrayList<Object>> insertList = new ArrayList<>();
		ArrayList<ArrayList<Object>> updateList = new ArrayList<>();
		String sql;
		StringBuilder kGramContent;
		mysqlDBInterface mysqlDBInterface = new mysqlDBInterface();
		mysqlDBInterface.connectToDB(db_ip, db_port, db_name, db_pwd);
		
		// 1.2.初始化k_gram表
		for( Entry<String, ArrayList<Object>> entry : k_gram_map.entrySet() ){
			
			// 需要处理sequence、content字段
			ArrayList<Object> kGram_Posting = new ArrayList<>();
			// 标记k_gram字段
			kGram_Posting.add(entry.getKey());
			// 标记k_gram_hash字段
			kGram_Posting.add(getTermHash(entry.getKey()));
			// 根据sequence值降序来保证返回的第一条数据是content内容尚未满的
			sql = "select id,number,content from " + db_kgramIndex 
					+ " where kgram_hash = " + getTermHash(entry.getKey())
					+ " order by number desc";
			ArrayList<ArrayList<Object>> resultSet = mysqlDBInterface.excuteSql(sql, 3);
			// content的结构为 <termId1, termId2>
			ArrayList<Object> value = entry.getValue();
			kGramContent = getKGramContent(value);
			ArrayList<StringBuilder> kGramContentHandling = new ArrayList<>();
			// 若词项在该文档中的倒排记录表超过 1024 需额外进行处理
			while (kGramContent.length() > 1024) {
				int toIndex = 1024*value.size()/kGramContent.length();
				StringBuilder temp = getKGramContent(mSublist(value,0,toIndex));
				while (temp.length() > 1024) {
					toIndex-=2;
					temp = getKGramContent(mSublist(value,0,toIndex));
				}
				kGramContentHandling.add(temp);
				value = mSublist(value, toIndex, value.size());
				kGramContent = getKGramContent(value);
			}
			// 若词项在该文档中的倒排记录表小于 1024 ，为了泛化性，依然加入arraylist中便于后续程序的统一
			kGramContentHandling.add(kGramContent);
			if(resultSet.get(0).size() == 0){
				// 数据库中尚未出现过这个词
				for(int k=0; k < kGramContentHandling.size(); k++){
					ArrayList<Object> temp = (ArrayList<Object>) kGram_Posting.clone();
					temp.add(k+1);   // sequence 置为1
					temp.add(kGramContentHandling.get(k).toString());    // 设置content字段
					// 放到待insert数组中
					insertList.add(temp);
				}
				
			}else{
				// 数据库中曾经出现过这个词
				StringBuilder judgeContentLength = spliceKgramContent((String)(resultSet.get(2).get(0)),
											(String)(resultSet.get(2).get(0)));
				int k=0;
				if(judgeContentLength.length() <= 1024){
					k=1;
					// 1. 最后一条记录是否能够容纳下此次的content，即合并后长度不大于1024
					ArrayList<Object> temp = (ArrayList<Object>) kGram_Posting.clone();
					temp.add(Integer.parseInt((String)(resultSet.get(1).get(0))) ); // 记录 sequence值
					temp.add(judgeContentLength.toString());  // 设置content字段
					temp.add(resultSet.get(0).get(0));    // 记录id值，便于update
					// 放到待update数组中
					updateList.add(temp);
				}
				for( ; k<kGramContentHandling.size(); k++) {
					// 2. 最后一条记录无法容纳此次的content，需另外insert一条记录
					ArrayList<Object> temp = (ArrayList<Object>) kGram_Posting.clone();
					temp.add(Integer.parseInt((String)(resultSet.get(1).get(0)))+k+1);  // 记录 sequence值
					temp.add(kGramContentHandling.get(k).toString());  // 设置content字段
					// 放到待insert数组中
					insertList.add(temp);
				}
			}	
		}	
		// 当每篇文章处理结束后，在本地将所要修改后的数据库插入格式写好，一次性插入，以便回滚
		// 1.处理k_gram表
		ArrayList<String> insertColumnName = new ArrayList<>();
		insertColumnName.add("kgram");
		insertColumnName.add("kgram_hash");
		insertColumnName.add("number");
		insertColumnName.add("content");
		
		mysqlDBInterface.quickInsertInBatch("INSERT", db_kgramIndex, insertColumnName, insertList);
		
		insertColumnName.add("id");
		int updateNum = mysqlDBInterface.quickUpdateForIR("UPDATE", db_kgramIndex, insertColumnName, updateList);
		System.out.println("2-gram表格装载成功");
//		System.out.println("k_gram updateNum hope = " + updateList.size() + " real = " + updateNum);	
		
		// 2.处理dictionary表
		dictionarySystem dictionarySystem = new dictionarySystem(db_ip, db_port, db_name, db_pwd, db_dictionary);
		// dictionaryHandled只包含termID
		ArrayList<Object> dictionaryHandled = dictionaeyNotHandled.get(0);
		dictionarySystem.setDictionaryHandled(dictionaryHandled);
		
		// 关闭mysql数据库流
		mysqlDBInterface.closeDB();
	}

	private StringBuilder getKGramContent(ArrayList<Object> value) {
		
		StringBuilder temp = new StringBuilder();

		temp.append("<");
		temp.append(value.get(0));
		for(int j=1; j<value.size(); j++){
			temp.append(",");
			temp.append(value.get(j));      // 表明当前处理的词项在文章中的位置
		}
		temp.append(">");
		
		return temp;
	}

	/**
	 * @param value 
	 * @param fromIndex
	 * @param toIndex
	 * @return 截取arraylist中的某段位置上的内容，并返回一个arraylist
	 * 是因为arraylist的sublist方法返回的结果无法强制转为arraylist类型，故采用此函数来实现本程序所需的内容
	 */
	public ArrayList<Object> mSublist(ArrayList<Object> value, int fromIndex, int toIndex) {
		ArrayList<Object> ans = new ArrayList<>();
		
		for(int i=fromIndex; i<toIndex; i++){
			ans.add(value.get(i));
		}
		
		return ans;
	}

	private StringBuilder spliceKgramContent(String oldContent, String newContent) {
		
		StringBuilder anStringBuilder = new StringBuilder();
		
		anStringBuilder.append(oldContent.substring(0, oldContent.length()-1));
		anStringBuilder.append(",");
		anStringBuilder.append(newContent.substring(1,newContent.length()));
		
		return anStringBuilder;
	}
}
