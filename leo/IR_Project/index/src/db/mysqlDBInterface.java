package db;

import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Statement;
import java.util.ArrayList;

public class mysqlDBInterface {
	
	public Connection con = null;
	private PreparedStatement pStatement = null;

    private final int ROWS_OF_SINGLE_BATCH = 1;
    private final int BATCHES_OF_SINGLE_TRANSACTION = 1;

    private int nCommit = 0;
	
	/**
	 * @param db_ip 数据库mysql的ip地址
	 * @param db_port  数据库mysql的端口号
	 * @param db_name  数据库mysql的用户名
	 * @param db_pwd  数据库mysql的密码
	 * @return 返回连接成功的Connection
	 */
	public void connectToDB(String db_ip, int db_port, String db_name, String db_pwd){

        // 驱动程序名
        String driver = "com.mysql.jdbc.Driver";
        // URL指向要访问的数据库名 test
        String url = "jdbc:mysql://" + db_ip + ":" + db_port;

        try {
            // 加载驱动程序
            Class.forName(driver);
            // getConnection()方法，连接MySQL数据库！！
            // "?rewriteBatchedStatements=true" 若不置为true，则批处理操作不执行
            // "useServerPrepStmts=true" 若不置为true，则预编译无效果
            con = DriverManager.getConnection
                    (url+ "?rewriteBatchedStatements=true&autoReconnect=true&failOverReadOnly=false&useUnicode=true&characterEncoding=utf8",
                            db_name,
                            db_pwd);
            // 关闭自动提交，以防插入大量数据时速度变慢
            con.setAutoCommit(false);

//            System.out.println("成功登陆MySQL数据库。");

        } catch (ClassNotFoundException e) {
            System.out.println("数据库驱动类异常，无法打开数据库。");
            e.printStackTrace();
        } catch (SQLException e) {
            System.out.println("数据库连接失败，无法打开数据库。");
            e.printStackTrace();
        }

    }
	
	 /**
	  * 若调用connectToDB函数，则之后必须调用该函数来正确关闭mysql连接，从而不影响mysql的性能
	 * @throws SQLException 
	 */
	public void closeDB(){
	    try {
			if (!con.isClosed())
				con.close();
		} catch (SQLException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		}
	 }

	/**
	 * 较quickInsertInBatch(String insertMethod,String tableName,
	 *                     ArrayList<String> insertColumnName,ArrayList<ArrayList<Object>> list,
                           int ROWS_OF_SINGLE_BATCH,int BATCHES_OF_SINGLE_TRANSACTION)
                     函数缺少了最后两个参数，做默认参数
	 * @param insertMethod
	 * @param tableName
	 * @param insertColumnName
	 * @param list
	 */
	public void quickInsertInBatch(String insertMethod,String tableName,ArrayList<String> insertColumnName,ArrayList<ArrayList<Object>> list){
		quickInsertInBatch(insertMethod, tableName, insertColumnName, list, ROWS_OF_SINGLE_BATCH, BATCHES_OF_SINGLE_TRANSACTION);
	}
	
    /**
     * @param insertMethod 操作数据表的方法，或insert或update或delete等
     * @param tableName   操作的数据表名
     * @param insertColumnName   操作的具体数据列，insertColumnName.size() = 0  则按默认的表结构插入
     * @param list  待插入的数据
     * @param ROWS_OF_SINGLE_BATCH 批量插入的行数
     * @param BATCHES_OF_SINGLE_TRANSACTION  每个事务中包含的批量插入次数
     */
    public void quickInsertInBatch(String insertMethod,String tableName,ArrayList<String> insertColumnName,ArrayList<ArrayList<Object>> list,
                                   int ROWS_OF_SINGLE_BATCH,int BATCHES_OF_SINGLE_TRANSACTION){

    	if(list.size() == 0)
    		return;
    	
        try {

            int sqlRecordNum = sqlRecordCount(list.size());

            ArrayList<Object> tempList = list.get(0);
            int columnCount = tempList.size();


//             构造长sql语句，加快插入数据库的速度
            StringBuilder sql =  createSql(insertMethod,tableName,
                    insertColumnName,columnCount,
                    sqlRecordNum);

            pStatement = con.prepareStatement(sql.toString());

            for(int i=0;i<list.size()/sqlRecordNum;i++){
                for(int j=0;j<sqlRecordNum;j++){
                    for(int k=0;k<columnCount;k++){
                        pStatement.setString(j*columnCount+k+1, "" + list.get(i*sqlRecordNum+j).get(k));
                    }
                }
                pStatement.addBatch();

                // 每maxBatch行执行插入
                if(i % ROWS_OF_SINGLE_BATCH == 0){
                    // 避免内存溢出
                    pStatement.executeBatch();
                    pStatement.clearBatch();

                    nCommit ++;
                    // 每maxCommit次插入后执行commit
                    if(nCommit % BATCHES_OF_SINGLE_TRANSACTION == 0){
                        con.commit();
                    }
                }

            }

            int temp = list.size() % sqlRecordNum;
            if(temp > 0 ){
                pStatement.executeBatch();
                // close pstatement otherwise the heap space will grow
                con.commit();
                pStatement.close();

                sql = createSql(insertMethod,tableName,insertColumnName,columnCount,temp);
                pStatement = con.prepareStatement(sql.toString());
                for(int i= (list.size()/sqlRecordNum) * sqlRecordNum,j = 0 ; i<list.size();i++){
                    for(int k=0;k<columnCount;k++,j++){
                        pStatement.setString(j+1, "" + list.get(i).get(k));
                    }
                }
                pStatement.addBatch();
            }

            pStatement.executeBatch();
            con.commit();

            pStatement.close();
            
//            System.out.println("insert success");

        } catch (SQLException e) {
            // TODO Auto-generated catch block
            System.out.println("wrong sql: " + pStatement);
            System.out.println("插入数据库失败。");

            e.printStackTrace();
        }
    }

    public int quickUpdateForIR(String insertMethod, String tableName, ArrayList<String> insertColumnName,ArrayList<ArrayList<Object>> list) {
		
    	int updateNum = 0;
    	
    	StringBuilder sql = new StringBuilder();
    	sql.append(insertMethod);
    	sql.append(" ");
    	sql.append(tableName);
    	sql.append(" SET ");
    	StringBuilder updateSQL;
    	ArrayList<Object> updateList;
    	for(int k=0; k<list.size(); k++){
    		updateList = list.get(k);
    		updateSQL = new StringBuilder(sql);
    		updateSQL.append(insertColumnName.get(2));
			updateSQL.append(" = \"");
    		updateSQL.append(updateList.get(2));
    		updateSQL.append("\"");
    		for(int i=3; i<(insertColumnName.size()-1); i++){
    			updateSQL.append(", ");
    			updateSQL.append(insertColumnName.get(i));
    			updateSQL.append(" = \"");
        		updateSQL.append(updateList.get(i));
        		updateSQL.append("\"");
        	}
    		updateSQL.append(" WHERE id = \"");
    		updateSQL.append(updateList.get(updateList.size()-1));
    		updateSQL.append("\"");
    		updateNum += excuteUpdate(updateSQL.toString());
    	}
    	
    	return updateNum;
	}
    
    public int excuteUpdate(String sql) {
    	
    	int updateColumns = 0;
    	
    	try {
    		Statement statement = con.createStatement();
    		updateColumns = statement.executeUpdate(sql);
    		
    		con.commit();
    		statement.close();
    		
		} catch (SQLException e) {
			// TODO Auto-generated catch block
			System.out.println("wrong sql : " + sql);
			e.printStackTrace();
		}
    	
		return updateColumns;
	}
    
    /**
     * @param sql 待执行的SQL语句
     * @param columnTotal 需返回的列数
     * @return
     */
    public ArrayList<ArrayList<Object>> excuteSql(String sql,int columnTotal) {
    	
    	ArrayList<ArrayList<Object>> temp = new ArrayList<ArrayList<Object>>();
    	
        try {
            Statement statement = con.createStatement();
            ResultSet resultSet = statement.executeQuery(sql);
            
         // 将 Arraylist 初始化，便于后续的使用
        	for(int i=0;i<columnTotal;i++)
        		temp.add(new ArrayList<Object>());
            
            while(resultSet.next()){
            	for(int i=0;i<columnTotal;i++)
            		temp.get(i).add(resultSet.getString(i+1));
            }

            resultSet.close();
            statement.close();
            
        } catch (SQLException e) {
            System.out.println("wrong sql: " + sql);
            System.out.println("操作数据库失败。");
            e.printStackTrace();
        }
        
        return temp;
    }
    
    /**
     * @param size 待操作的数据行数
     * @return 每条长SQL语句的长度
     * my.cnf 中 max_allowed_packet = 16M，即长sql语句的长度限制为 16M
     */
    private int sqlRecordCount(int size){
        if(size > 5)
            return 5;
        return 1;
    }

    /**
     * 作用：构造长sql语句，加快插入数据库的速度
     * @param insertMethod 
     * @param tableName
     * @param insertColumnName
     * @param columnCount
     * @param sqlRecordNum
     * @return  生成长SQL语句待填充模式
     */
    private StringBuilder createSql(String insertMethod,String tableName,ArrayList<String> insertColumnName,int columnCount,int sqlRecordNum){

        StringBuilder sql = new StringBuilder();
        sql.append(insertMethod);
        sql.append(" into ");
        sql.append(tableName);

        if(insertColumnName.size() > 0) {
            sql.append(" (");
            sql.append(insertColumnName.get(0));
            for (int i = 1; i < columnCount; i++) {
                sql.append(",");
                sql.append(insertColumnName.get(i));
            }
            sql.append(")");
        }

        sql.append(" values (?");
        for(int i=1;i<columnCount;i++){
            sql.append(",?");
        }
        sql.append(")");
        for(int i=1;i<sqlRecordNum;i++){
            sql.append(",(?");
            for(int j=1;j<columnCount;j++){
                sql.append(",?");
            }
            sql.append(")");
        }

        return sql;
    }
 
}
