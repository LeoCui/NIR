package postingList;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.Map.Entry;

import db.jsonUtils;
import db.mysqlDBInterface;
import db.utils;
import dictionary.dictionarySystem;
import net.sf.json.JSONObject;
import pre_processing.WordSeg;

public class postingListSystem {
	
	private String db_IP, db_user, db_password;
	private int db_port;
	private String db_news_info, db_contents_info, db_comment_info, db_postingList, db_dictionary, db_kgramIndex;
	private mysqlDBInterface mysqlDBInterface = new mysqlDBInterface();
	private dictionarySystem dictionarySystem;
	private utils utils = new utils();
	private WordSeg wordSeg = new WordSeg();
	
	/**
	 * 作用：解析MySQL参数文件
	 */
	public postingListSystem() {
		// 参数文件解析模块
        String jsonContext = new jsonUtils().ReadFile("config/postingList_dbInfo.json");
        JSONObject jsonObject = JSONObject.fromObject(jsonContext);
        // 1.获取MySQL参数
        JSONObject jsonMySQL = jsonObject.getJSONObject("MySQL_DBInfo");
        db_IP = jsonMySQL.getString("IP");
        db_port = jsonMySQL.getInt("port");
        db_user = jsonMySQL.getString("user");
        db_password = jsonMySQL.getString("password");
        // 2.获取每张数据表的具体位置
        db_news_info = jsonObject.getString("news_info");
        db_contents_info = jsonObject.getString("content_info");
        db_comment_info = jsonObject.getString("comment_info");
        db_postingList = jsonObject.getString("posting_list");
        db_dictionary = jsonObject.getString("dictionary_table");
        db_kgramIndex = jsonObject.getString("kgram_Index");
        // 3.处理dictionary表的填写
        dictionarySystem = new dictionarySystem(db_IP, db_port, db_user, db_password, db_dictionary);
	}
	
	/**
	 * 作用：初始化建立倒排记录表
	 */
	public void buildPostingList(){
		
		handlePostingList();
 		
 		System.out.println("posting list initialize successfully.");
	}	
	
	/**
	 * 作用：具体处理倒排记录表+k-gram表
	 */
	private void handlePostingList() {
		
		// 1.连接数据库
		mysqlDBInterface.connectToDB(db_IP, db_port, db_user, db_password);
		System.out.println("成功登陆MySQL数据库。");
		// 1.1.从 news_info 表中取出 is_handled=0  的 news_id_list
		String sql = "select id,title from " + db_news_info + " WHERE is_handled = 0";	
		ArrayList<ArrayList<Object>> resultSet = mysqlDBInterface.excuteSql(sql, 2);
		ArrayList<Object> news_id_not_handled = resultSet.get(0);
		ArrayList<Object> news_title_not_handled = resultSet.get(1);
		String doc = "";   // 待进行倒排记录表处理的文档内容（或为新闻正文、或为新闻评论）
		ArrayList<Object> comments_list;   // mysql中comment_info表相关新闻的评论列表（未处理）
		ArrayList<Object> comments;
		String comment_spliting;
		String[] splitArray1,splitArray2;
		int docHandlingNumber = news_id_not_handled.size();
//		int docHandlingNumber = 10000; 
		
		for(int i=0; i < docHandlingNumber; i++){
			
			// 2.具体处理每一条新闻（正文+评论）
			// 2.1.从 content_info 表中将每篇文章的具体正文内容读取出来
			sql = "SELECT content from "+ db_contents_info +" WHERE news_id = "
					+ news_id_not_handled.get(i) +" ORDER BY sequence_number";
			
			// 2.2.1.组装新闻正文
			doc = (String) news_title_not_handled.get(i);
			doc += " ";
			doc += utils.getDocByContentSequence(mysqlDBInterface.excuteSql(sql, 1).get(0));
			
			// 2.2.2.对新闻正文内容进行倒排记录
			handleDoc(doc, news_id_not_handled.get(i), 0);
			
			// 2.3.从 comment_info 表中将每篇文章的具体评论内容读取出来，将评论里每个用户的评论内容之间插一个空格来拼接进行倒排记录
			sql = "SELECT content from "+ db_comment_info +" WHERE news_id = "
					+ news_id_not_handled.get(i) +" ORDER BY id";
			comments_list = mysqlDBInterface.excuteSql(sql, 1).get(0);
			// 初始化，以防前一轮循环的结果影响了此轮
			comments = new ArrayList<>();   // 记录每条具体的评论内容
			
			for(int j=0; j<comments_list.size(); j++){
				comment_spliting = (String) comments_list.get(j);
				splitArray1 = comment_spliting.split("\\|");    // 用“|”作为分隔,分隔若干个评论
				for(int k=0; k<splitArray1.length; k++){
					// 每条评论的格式为“时间 用户 评论内容”，以空格作为分隔
					comment_spliting = splitArray1[k];
					splitArray2 = comment_spliting.split(" ");
					comments.add(splitArray2[splitArray2.length-1] + " ");
				}
			}
			doc = utils.getDocByContentSequence(comments);
			// 2.4.对新闻的评论内容进行倒排记录
			handleDoc(doc, news_id_not_handled.get(i), 1);
			
		}
		
		// 3.建立k-gram表，便于通配符查询
		utils.handleKGram(db_IP, db_port, db_user, db_password, db_dictionary, db_kgramIndex, 
				dictionarySystem.getDictionaryNotHandled());	
		
		// 4.标记该文章已处理
		StringBuilder setHandledSQL = new StringBuilder("UPDATE " + db_news_info + " SET is_handled = 1 WHERE id in (");
		setHandledSQL.append(news_id_not_handled.get(0));
		for(int i=1; i < docHandlingNumber; i++){
			setHandledSQL.append(",");
			setHandledSQL.append(news_id_not_handled.get(i));
		}
		setHandledSQL.append(")");
		
		System.out.println(setHandledSQL.toString());
 		System.out.println("共处理了  " + mysqlDBInterface.excuteUpdate(setHandledSQL.toString()) + " 篇新闻");
 			
 		// 5.关闭数据库流
 		mysqlDBInterface.closeDB();
	}
	
	/**
	 * @param doc 待处理的文档内容
	 * @param docID 待处理的文档标识符
	 * @param isNews 0 表明处理的是新闻； 1表明处理的是评论
	 * 用于处理倒排记录表
	 */
	@SuppressWarnings("unchecked")
	private void handleDoc(String doc, Object docID, int isNews) {
				
		// 1.1.将文章分词
		ArrayList<String> words =  wordSeg.segmentation(doc,true);
		HashMap<String, ArrayList<Object>> words_location_map = new HashMap<>();
		
		// 1.2.将分词结果去重,便于后续建立倒排记录表
		for(int j=0;j<words.size();j++){
			
			if(!words_location_map.containsKey(words.get(j))){
				ArrayList<Object> tempLocal = new ArrayList<>();
				tempLocal.add(j);
				words_location_map.put(words.get(j), tempLocal);
			}else {
				ArrayList<Object> tempLocal = words_location_map.get(words.get(j));
				tempLocal.add(j);
				words_location_map.replace(words.get(j), tempLocal);
			}
		}
		
		ArrayList<ArrayList<Object>> insertList = new ArrayList<>();
		ArrayList<ArrayList<Object>> updateList = new ArrayList<>();
		String sql;
		StringBuilder termContent;
		
		// 1.3.初始化倒排记录表
		for( Entry<String, ArrayList<Object>> entry : words_location_map.entrySet() ){
			
			// 需要处理df、number、content三个字段
			ArrayList<Object> term_Posting = new ArrayList<>();
			// 标记term字段
			term_Posting.add(entry.getKey());
			// 标记term_hash字段
			term_Posting.add(utils.getTermHash(entry.getKey()));
			// 根据id值降序来保证返回的第一条数据是content内容尚未满的
			sql = "select id,df,sequence,content from " + db_postingList 
					+ " where term_hash = " + utils.getTermHash(entry.getKey())
					+ " order by sequence desc";
			ArrayList<ArrayList<Object>> resultSet = mysqlDBInterface.excuteSql(sql, 4);
			// content的结构为 0/1  docID  <position1,position2>
            // 不同文档之间用|分开其中:
            // 0表示新闻（news_info表），1表示评论（comment_info表）
            // 如： 0  34  <1,5,8>|1  45  <3,4>
			ArrayList<Object> value = entry.getValue();
			termContent = getTermContent(isNews, docID, value);
			ArrayList<StringBuilder> termContentHandling = new ArrayList<>();
			// 若词项在该文档中的倒排记录表超过 1024 需额外进行处理
			while (termContent.length() > 1024) {
				int toIndex = 1024*value.size()/termContent.length();
				StringBuilder temp = getTermContent(isNews, docID, utils.mSublist(value,0,toIndex));
				while (temp.length() > 1024) {
					toIndex-=2;
					temp = getTermContent(isNews, docID, utils.mSublist(value,0,toIndex));
				}
				termContentHandling.add(temp);
				value = utils.mSublist(value, toIndex, value.size());
				termContent = getTermContent(isNews, docID, value);
			}
			// 若词项在该文档中的倒排记录表小于 1024 ，为了泛化性，依然加入arraylist中便于后续程序的统一
			termContentHandling.add(termContent);
			if(resultSet.get(0).size() == 0){
				// 数据库中尚未出现过这个词
				for(int k=0; k < termContentHandling.size(); k++){
					ArrayList<Object> temp = (ArrayList<Object>) term_Posting.clone();
					temp.add(1);   // df 置为1
					temp.add(k+1);   // number 置为1
					temp.add(termContentHandling.get(k).toString());    // 设置content字段
					// 放到待insert数组中
					insertList.add(temp);
				}
				
			}else{
				// 数据库中曾经出现过这个词
				StringBuilder judgeContentLength = new StringBuilder((String)(resultSet.get(3).get(0)));
				judgeContentLength.append("|");
				judgeContentLength.append(termContentHandling.get(0).toString());
				int k=0;
				if(judgeContentLength.length() <= 1024){
					k=1;
					// 1. 最后一条记录是否能够容纳下此次的content，即合并后长度不大于1024
					ArrayList<Object> temp = (ArrayList<Object>) term_Posting.clone();
					temp.add(Integer.parseInt((String)resultSet.get(1).get(0))+1);  // 记录 df值
					temp.add(Integer.parseInt((String)(resultSet.get(2).get(0))) ); // 记录 number值
					temp.add(judgeContentLength.toString());  // 设置content字段
					temp.add(resultSet.get(0).get(0));    // 记录id值，便于update
					// 放到待update数组中
					updateList.add(temp);
				}
				for( ; k<termContentHandling.size(); k++) {
					// 2. 最后一条记录无法容纳此次的content，需另外insert一条记录
					ArrayList<Object> temp = (ArrayList<Object>) term_Posting.clone();
					temp.add(1);  // 记录 df 值
					temp.add(Integer.parseInt((String)(resultSet.get(2).get(0)))+k+1);  // 记录 number值
					temp.add(termContentHandling.get(k).toString());  // 设置content字段
					// 放到待insert数组中
					insertList.add(temp);
				}
			}	
		}	
		// 当每篇文章处理结束后，在本地将整篇文章所要修改后的数据库插入格式写好，一次性插入，以便回滚
		// 1.处理postingList
		ArrayList<String> insertColumnName = new ArrayList<>();
		insertColumnName.add("term");
		insertColumnName.add("term_hash");
		insertColumnName.add("df");
		insertColumnName.add("sequence");
		insertColumnName.add("content");
		
		mysqlDBInterface.quickInsertInBatch("INSERT", db_postingList, insertColumnName, insertList);
		
		insertColumnName.add("id");
//		int updateNum = mysqlDBInterface.quickUpdateForIR("UPDATE", db_postingList, insertColumnName, updateList);
		mysqlDBInterface.quickUpdateForIR("UPDATE", db_postingList, insertColumnName, updateList);
		//		System.out.println("updateNum hope = " + updateList.size() + " real = " + updateNum);	
		// 2.处理dictionary表
		ArrayList<ArrayList<Object>> dictionary = new ArrayList<>();
		for(ArrayList<Object> item : insertList){
			// 只保留term 、 term_hash两个字段
			dictionary.add(utils.mSublist(item, 0, 2));
		}
		dictionarySystem.putDictionary(dictionary);
	}
	
	/**
	 * 作用：新增网页时更新posting_list表
	 */
	public void updatePostingList(){
		
		handlePostingList();
		
		System.out.println("posting list update successfully.");
	}
	
	/**
	 * 先不做
	 * 当某个网页被删除时，需要将posting_list表中含有该网页的记录删除，
	 * @param docID
	 */
	public void deleteDocInPostingList(int docID){
		
	}

	/**
	 * @param isNews 枚举，0表示新闻，1表示评论
	 * @param docID 该文档ID
	 * @param value 词项在该文档中的位置记录
	 * @return 构造词项在该文档中的倒排记录表具体内容
	 */
	private StringBuilder getTermContent(int isNews, Object docID, ArrayList<Object> value) {
		
		StringBuilder temp = new StringBuilder();
		
		temp.append(isNews);   // 表明是在处理新闻正文
		temp.append(" ");
		temp.append(docID);   // 表明处理的是news_id_not_handled第i篇文章
		temp.append(" ");
		temp.append(value.size());      // 记录 tf 值
		temp.append(" <");
		temp.append(value.get(0));
		for(int j=1; j<value.size(); j++){
			temp.append(",");
			temp.append(value.get(j));      // 表明当前处理的词项在文章中的位置
		}
		temp.append(">");
		
		return temp;
	}
	
}
