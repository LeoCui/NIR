package pre_processing;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileInputStream;
import java.io.InputStreamReader;
import java.util.ArrayList;
import java.util.List;

import com.hankcs.hanlp.HanLP;
import com.hankcs.hanlp.seg.common.Term;

public class WordSeg {
	
	private static ArrayList<String> stopWord = new ArrayList<>();
	
	public WordSeg() {
		
		readStopWord();   // 读入停用词表
	}
	
	/**
	 * 读入停用词表
	 */
	private void readStopWord() {
		
		File file = new File("config/stopWord.txt");
		try{
			// 需要指定读入的文件以 gbk 编码打开，因为 OS 系统下文件创建时的默认编码为 gbk, 而IDE的默认编码为 utf-8
			InputStreamReader read = new InputStreamReader(new FileInputStream(file),"gbk");
            BufferedReader br = new BufferedReader(read);//构造一个BufferedReader类来读取文件
            String s = null;
            while((s = br.readLine())!=null){//使用readLine方法，一次读一行
                stopWord.add(s);
            }
            br.close();    
        }catch(Exception e){
            e.printStackTrace();
        }
		
		System.out.println("stopWord read successfully.");
        
	}

//	public static void main(String[] args) {
//		
//		List<Term> aStrings = HanLP.segment("你好，欢迎来到CCTV5直播间我是主播杨戬！");
//		System.out.println(aStrings);
//		System.out.println(aStrings.get(0).word + " " + aStrings.get(2).offset + " " + aStrings.get(0).nature);
//	}
	
	
	/**
	 * @param str 待分词的句子或文章
	 * @return  返回分词结果
	 */
	public ArrayList<String> segmentation(String str, boolean useStopWord){
		List<Term> terms = HanLP.segment(str);
		
		ArrayList<String> words = new ArrayList<>();
		for(Term term : terms){
			words.add(term.word);
		}
		
		ArrayList<String> words_UnderStopWord = new ArrayList<>();
		if(useStopWord){
			// 确认使用停用词表
			for(int k=0; k<terms.size(); k++){
				if (!stopWord.contains(words.get(k))) {
					// 若该词在停用词表中出现过,则删除该词	
					words_UnderStopWord.add(words.get(k));
				}
			}
			return words_UnderStopWord;
		}else {
			// 不使用停用词
			return words;
		}		
		
	}
}
