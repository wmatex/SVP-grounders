/*
 * Copyright (c) 2015 Ondrej Kuzelka
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
 */

package metacentrum;

import lrnn.learning.Result;
import lrnn.learning.Results;

import java.io.File;
import java.io.FileNotFoundException;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Scanner;

/**
 * Created by gusta on 19.10.17.
 */
public class Aleph {

    static String metaStorage = "/storage/plzen1/home/souregus/aleph";

    public static void main(String[] args) throws IOException {
        readResults();
        //writeScripts();
    }

    public static void readResults() {
        String datasetsPath = "/media/gusta/00EA8E2AEA8E1C52/data/Aleph/muta_ptc";
        //Map<String, Double> stringDoubleMap = ReadAlephResults(datasetsPath, "mln");
        Map<String, Double> stringDoubleMap = ReadRDNResults(datasetsPath, "muta_ptc");
        printMap(stringDoubleMap);
    }

    private static void printMap(Map<String, Double> stringDoubleMap) {
        for (Map.Entry ent : stringDoubleMap.entrySet()) {
            System.out.println(ent);
        }
    }

    public static void writeScripts() throws IOException {
        String datasetsPath = "/home/gusta/googledrive/NeuraLogic/datasets/NCI";
        RDNboost(datasetsPath, "muta_ptcTrees", "-XX:NewSize=1000m -Xms1900m -Xmx2g", "");
        Aleph(datasetsPath, "muta_ptcTrees", "");
    }

    public static void RDNboost(String datasetsPath, String experimentDir, String javaParams, String rdnParams) throws IOException {

        String metacentrumPath = "../metacentrum/RDNboost/" + experimentDir;
        new File(metacentrumPath).mkdirs();
        StringBuilder qsub = new StringBuilder();

        File[] files = new File(datasetsPath).listFiles();
        for (File dir : files) {
            if (!dir.isDirectory()) continue;
            StringBuilder script = new StringBuilder();
            script.append("module add jdk-8\nexport OMP_NUM_THREADS=1\nsleep 60\n");

            File[] folds = dir.listFiles();
            for (File fold : folds) {
                if (fold.isFile()) continue;
                if (!fold.getName().startsWith("fold")) continue;
                script.append("cd " + metaStorage + "/datasets/" + experimentDir + "/" + dir.getName() + "/" + fold.getName() + "\n");
                script.append("java  -XX:+UseSerialGC -XX:-BackgroundCompilation -Djava.util.concurrent.ForkJoinPool.common.parallelism=1 -Daffinity.reserved=1  " + javaParams + " -jar ");
                script.append(metaStorage + "/BoostSRL.jar -l -train ./train -model ./train/models_" + experimentDir + " -target active " + rdnParams + " -modelSuffix " + experimentDir + " > /dev/null\n");

                script.append("java  -XX:+UseSerialGC " + javaParams + " -jar ");
                script.append(metaStorage + "/BoostSRL.jar -i -model ./train/models_" + experimentDir + " -test ./test -target active " + rdnParams + " -aucJarPath " + metaStorage + " -modelSuffix " + experimentDir + "\n");
            }
            Files.write(Paths.get(metacentrumPath + "/" + dir.getName() + ".sh"), script.toString().getBytes());
            qsub.append("qsub -l select=1:ncpus=1:mem=2gb -l walltime=2:00:00 " + "  ./" + dir.getName() + ".sh\n");
        }
        Files.write(Paths.get(metacentrumPath + "/qsub.sh"), qsub.toString().getBytes());
    }

    public static void Aleph(String datasetsPath, String experimentDir, String alephParams) throws IOException {
        String yapPath = metaStorage + "/yap-6.2.2";
        String alephPath = metaStorage + "/aleph.pl";
        String metacentrumPath = "../metacentrum/Aleph/" + experimentDir;
        new File(metacentrumPath).mkdirs();
        StringBuilder qsub = new StringBuilder();

        File[] files = new File(datasetsPath).listFiles();
        for (File dir : files) {
            if (!dir.isDirectory()) continue;
            StringBuilder script = new StringBuilder();

            File[] folds = dir.listFiles();
            for (File fold : folds) {
                if (fold.isFile()) continue;
                if (!fold.getName().startsWith("fold")) continue;

                script.append("cd " + yapPath + "\n");
                String dataPath = metaStorage + "/datasets/" + experimentDir + "/" + dir.getName() + "/" + fold.getName();
                script.append("echo \"read_all('" + dataPath + "/train'). set(test_pos, '" + dataPath + "/test.f'). set(test_neg, '" + dataPath + "/test.n'). set(recordfile, '" + dataPath + "/aleph_" + experimentDir + ".trace')." + alephParams + " induce.\" | " + yapPath + "/yap -l " + alephPath + " > /dev/null\n");
            }
            Files.write(Paths.get(metacentrumPath + "/" + dir.getName() + ".sh"), script.toString().getBytes());
            qsub.append("qsub -l select=1:ncpus=1:mem=2gb -l walltime=24:00:00 " + "  ./" + dir.getName() + ".sh\n");
        }
        Files.write(Paths.get(metacentrumPath + "/qsub.sh"), qsub.toString().getBytes());
    }

    public static Map<String, Double> ReadRDNResults(String path, String experimentDir) {
        Map<String, Double> results = new HashMap<>();
        File[] files = new File(path).listFiles();
        for (File dir : files) {
            double testAccuracy = 0;
            double testAccuracy2 = 0;
            int foldCount = 0;
            int foldCount2 = 0;
            if (!dir.isDirectory()) continue;
            File[] folds = dir.listFiles();
            for (File fold : folds) {
                if (fold.getName().startsWith("fold")) {
                    File[] fs = new File(fold + "/test").listFiles();
                    if (fs != null) {
                        Double add = ReadRDNResultsFromFile(new File(fold + "/test/test_infer" + experimentDir + "_dribble.txt"));
                        if (add != null && !Double.isNaN(add)) {
                            testAccuracy += add;
                            foldCount++;
                        }
                        for (File f : fs) {
                            if (f.getName().startsWith("results_" + experimentDir)) {
                                add = readRDNresultsFromAUC(f);
                                if (add != null && !Double.isNaN(testAccuracy)) {
                                    testAccuracy2 += add;
                                    foldCount2++;
                                }
                            }
                        }
                    }
                }
            }
            if (!Double.isNaN(testAccuracy)) {
            //    results.put(dir.getName(), testAccuracy / foldCount);
            }
            if (!Double.isNaN(testAccuracy)) {
                results.put(dir.getName() + "", testAccuracy2 / foldCount2);
            }
        }
        return results;
    }

    private static Double readRDNresultsFromAUC(File f) {
        Results results = new Results();
        try {
            List<String> lines = Files.readAllLines(f.toPath());
            for (String line : lines) {
                if (line.isEmpty()) continue;
                String[] split = line.split(" ");
                if (split[0].startsWith("!")) {
                    results.add(new Result(1 - Double.parseDouble(split[1]), 0));
                } else {
                    results.add(new Result(Double.parseDouble(split[1]), 1));
                }
            }
            results.computeTrain();
            results.training = results.actualResult;
            //results.training.setThresh(0.5);
            results.computeTest();
            results.testing = results.actualResult;
            return 1 - results.testing.getError();
        } catch (IOException e) {
            //return null;
            //e.printStackTrace();
        }
        return null;
    }

    private static Double ReadRDNResultsFromFile(File f) {
        double precision = 0;
        double recall = 0;
        double allPos = 0;
        double allNeg = 0;

        try {
            List<String> lines = Files.readAllLines(f.toPath());
            for (String line : lines) {
                if (line.contains("%Pos=")) {
                    allPos = Double.parseDouble(line.split("=")[1]);
                }
                if (line.contains("%Neg=")) {
                    allNeg = Double.parseDouble(line.split("=")[1]);
                }
                if (line.contains("Precision =")) {
                    precision = Double.parseDouble(line.split("\\s+")[3]);
                }
                if (line.contains("Recall    =")) {
                    recall = Double.parseDouble(line.split("\\s+")[3]);
                }
            }
        } catch (IOException e) {
            return null;
            //e.printStackTrace();
        }
        //calculation
        double tp = recall * allPos;
        double fp = 1 / precision * tp - tp;
        double tn = allNeg - fp;

        double accuracy = (tp + tn) / (allNeg + allPos);
        return accuracy;
    }

    public static Map<String, Double> ReadAlephResults(String path, String experiment) {
        Map<String, Double> results = new HashMap<>();
        File[] files = new File(path).listFiles();
        for (File dir : files) {
            double testAccuracy = 0;
            int foldCount = 0;
            if (!dir.isDirectory()) continue;
            File[] folds = dir.listFiles();
            for (File fold : folds) {
                if (fold.getName().startsWith("fold")) {
                    File[] fs = fold.listFiles();
                    for (File f : fs) {
                        if (f.getName().endsWith(experiment + ".trace")) {
                            Double add = ReadAlephResultsFromFile(f);
                            if (add != null) {
                                testAccuracy += add;
                                foldCount++;
                            }
                        }
                    }
                }
            }
            results.put(dir.getName(), testAccuracy / foldCount);
        }
        return results;
    }

    private static Double ReadAlephResultsFromFile(File f) {
        try {
            Scanner scanner = new Scanner(f);
            int lineNum = 0;
            boolean testPart = false;
            while (scanner.hasNextLine()) {
                String line = scanner.nextLine();
                lineNum++;
                if (line.contains("Test set performance")) {
                    testPart = true;
                }
                if (testPart && line.contains("Accuracy = ")) {
                    return Double.parseDouble(line.split(" ")[2]);
                }
            }
        } catch (FileNotFoundException e) {
        }
        return null;
    }

}
