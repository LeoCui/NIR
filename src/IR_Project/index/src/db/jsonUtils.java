package db;

import java.io.*;

public class jsonUtils {
	
	/**
	 * 作用：读入配置文件
	 * @param path 文件位置
	 * @return
	 */
	public String ReadFile(String path){
        BufferedReader reader = null;
        String lastStr = "";
        try {
            FileInputStream fileInputStream = new FileInputStream(path);
            InputStreamReader inputStreamReader = new InputStreamReader(fileInputStream);
            reader = new BufferedReader(inputStreamReader);
            String tempStr = null;
            while( ( tempStr = reader.readLine() ) != null){
                lastStr += tempStr;
            }
            reader.close();
        } catch (FileNotFoundException e) {
            e.printStackTrace();
        } catch (IOException e) {
            e.printStackTrace();
        }finally {
            if(reader != null)
                try {
                    reader.close();
                } catch (IOException e) {
                    e.printStackTrace();
                }
        }

        return lastStr;
    }
}
