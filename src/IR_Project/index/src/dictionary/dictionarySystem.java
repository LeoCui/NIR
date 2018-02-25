package dictionary;

import java.util.ArrayList;

import db.mysqlDBInterface;

public class dictionarySystem {
	
	private mysqlDBInterface mysqlDBInterface = new mysqlDBInterface();
	private String tableName;
	
	public dictionarySystem(String db_ip, int db_port, String db_name, String db_pwd,String tableName) {
		this.tableName = tableName;
		
		mysqlDBInterface.connectToDB(db_ip, db_port, db_name, db_pwd);
	}
	
	/**
	 * @param dictionary 内含两个arraylist，分别为term，termHash
	 * @return 
	 */
	public int putDictionary(ArrayList<ArrayList<Object>> dictionary) {
		// 成功存入dictionary表的数目
		int putNum = 0;
		
		// 1.去除传进来的参数dictionary中已在数据库中存在的词项
		dictionary = rmDuplicateInDatabase(dictionary);
		// 2.将数据插入数据库中
		// 2.1.连接数据库流
		
		// 2.2.将数据插入数据库中
		ArrayList<String> insertColumnName = new ArrayList<>();
		insertColumnName.add("term");
		insertColumnName.add("term_hash");
		mysqlDBInterface.quickInsertInBatch("INSERT", tableName, insertColumnName, dictionary);
		// 2.2.断开数据库流
//		mysqlDBInterface.closeDB();
		
		// 返回成功存入dictionary表的数目
		return putNum;
	}
	
	/**
	 * @return 获取dictionary表格中的termID、term
	 */
	public ArrayList<ArrayList<Object>> getDictionaryNotHandled() {
		// ans.get(0) -> termID
		// ans.get(1) -> term
		ArrayList<ArrayList<Object>> ans;
		
		String sql = "SELECT id,term from " + tableName + " where is_handled = 0";
		
		ans = mysqlDBInterface.excuteSql(sql, 2);
		
		return ans;
	}
	
	/**
	 * @param dictionary
	 * @return 去除传进来的参数dictionary中已在数据库中存在的词项
	 */
	private ArrayList<ArrayList<Object>> rmDuplicateInDatabase(ArrayList<ArrayList<Object>> dictionary) {
		// 去除已在数据库中存在的词项
		ArrayList<ArrayList<Object>> dictionary_ans = dictionary;
		
		//
		String sql = "SELECT term,term_hash from " + tableName; 
		ArrayList<ArrayList<Object>> resultSet = mysqlDBInterface.excuteSql(sql, 2);
		for(ArrayList<Object> item : resultSet){
			if(dictionary.contains(item))
				dictionary_ans.remove(item);
		}
		
		// 返回去除后的结果
		return dictionary_ans;
	}

	/**
	 * @param dictionaryHandled 已经处理完的dictionary
	 */ 
	public void setDictionaryHandled(ArrayList<Object> dictionaryHandled) {
		StringBuilder setHandledSQL = new StringBuilder("UPDATE " + tableName + " SET is_handled = 1 WHERE id in (");
		setHandledSQL.append(dictionaryHandled.get(0));
		for(int i=1; i < dictionaryHandled.size(); i++){
			setHandledSQL.append(",");
			setHandledSQL.append(dictionaryHandled.get(i));
		}
		setHandledSQL.append(")");
		
		System.out.println("dictionary表装载成功");
//		System.out.println(setHandledSQL.toString());
// 		System.out.println("dictionary set handled updateNum = " + mysqlDBInterface.excuteUpdate(setHandledSQL.toString()));
	}
}
