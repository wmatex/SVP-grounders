package lrnn.crossvalidation;

import lrnn.construction.example.Example;
import lrnn.global.Global;
import lrnn.global.Glogger;
import lrnn.learning.Sample;

import java.io.*;
import java.nio.file.Files;
import java.util.ArrayList;
import java.util.Collections;
import java.util.LinkedList;
import java.util.List;
import java.util.logging.Level;
import java.util.logging.Logger;
import java.util.stream.Collectors;

/**
 * Splitter for performing stratified n-fold crossval
 */
public class SampleSplitter implements Serializable {

    public int foldCount;
    public int testFold = 0;
    public List<List<Sample>> folds;
    public List<Sample> samples;

    public SampleSplitter(File[] foldsPaths) {
        folds = new ArrayList<>();
        samples = new ArrayList<>();
        for (File path : foldsPaths) {
            try {
                List<Sample> samples = Files.lines(new File(path + "/test.txt").toPath()).map(line ->
                        new Sample(new Example(line.substring(line.indexOf(" ") + 1) + (line.charAt(line.length() - 1) == '.' ? "" : ".")), line.substring(0, line.indexOf(" ")).matches("[1\\+]") ? 1.0 : 0.0))
                        .collect(Collectors.toList());
                folds.add(samples);
                samples.addAll(samples);
            } catch (IOException e) {
                e.printStackTrace();
            }
        }
        foldCount = foldsPaths.length;
    }

    public SampleSplitter(List<Sample> train, List<Sample> test) {
        folds = new ArrayList<>();
        numberSamples(train);
        numberSamples(test);
        folds.add(train);
        folds.add(test);
        testFold = 1;
        foldCount = 1; //should be checked
        samples = new ArrayList<>(train.size() + test.size());
        samples.addAll(train);
        samples.addAll(test);
    }

    /**
     * stratified split of examples(same #positive examples) for k-fold
     * cross-validation
     *
     * @param k
     * @param ex
     */
    public SampleSplitter(int k, List<Sample> ex) {
        numberSamples(ex);

        folds = new ArrayList<>();
        samples = new ArrayList<>();
        samples.addAll(ex);

        Collections.shuffle(ex, Global.getRg()); //omg!!

        List<Sample> positives = getPositives(ex);
        List<Sample> negatives = getNegatives(ex);


        if (ex.size() < k) {
            Glogger.err("Too many fold and too few examples!!");
            return;
        }

        int foldLen = (int) Math.floor((double) ex.size() / k);
        //repaired fold count - extra fold for remaining samples
        foldCount = k;
        //foldCount = (int) Math.floor((double) ex.size() / foldLen);

        if (positives.size() + negatives.size() < samples.size()){
            for (int i = 0; i < foldCount; i++) {
                List<Sample> fold = new ArrayList<>();
                for (int j = 0; j < foldLen; j++) {
                    fold.add(samples.get(i*foldLen + j));
                }
                folds.add(fold);
            }
            return;
        }

        int positivesInFold = (int) Math.ceil((double) positives.size() / ex.size() * foldLen);

        int n = 0;
        int p = 0;

        while (n < negatives.size() || p < positives.size()) {
            List<Sample> fold = new ArrayList<>();
            for (int pNeeded = 0; pNeeded < positivesInFold && p < positives.size(); pNeeded++) {
                fold.add(positives.get(p++));
            }

            while (fold.size() < foldLen && n < negatives.size()) {
                fold.add(negatives.get(n++));
            }

            Collections.shuffle(fold, Global.getRg());
            folds.add(fold);
        }

        //distribute the last corrupted fold
        if (folds.size() > k) {
            int i = 0;
            for (Sample negative : folds.get(k)) {
                List<Sample> ff = folds.get(i++); //problem with retypeing
                ff.add(negative);
            }
            folds.remove(k);
        }

        if (Global.isOutputFolds()) {
            outputSplits(Global.outputFolder);
        }
    }

    public List<String> outputSplits(String path) {
        List<String> foldPaths = new ArrayList<>();
        Glogger.createDir(path + "/folds");
        int i = 1;
        for (List<Sample> fold : folds) {
            try {
                String foldPath = path + "/folds/fold" + i++;
                foldPaths.add(foldPath);
                BufferedWriter pw = new BufferedWriter(new OutputStreamWriter(new FileOutputStream(foldPath), "utf-8"));
                for (Sample exa : fold) {
                    pw.write(exa.targetValue + " " + exa.getExample().hash + "\n");
                    pw.flush();
                }
            } catch (FileNotFoundException ex1) {
                Logger.getLogger(SampleSplitter.class.getName()).log(Level.SEVERE, null, ex1);
            } catch (UnsupportedEncodingException ex1) {
                Logger.getLogger(SampleSplitter.class.getName()).log(Level.SEVERE, null, ex1);
            } catch (IOException ex1) {
                Logger.getLogger(SampleSplitter.class.getName()).log(Level.SEVERE, null, ex1);
            }
        }
        return foldPaths;
    }

    private List<Sample> getPositives(List<Sample> ex) {
        List<Sample> positives = new ArrayList<>();
        for (Sample e : ex) {
            if (e.getExample().getExpectedValue() == 1) {
                positives.add(e);
            }
        }

        return positives;
    }

    private List<Sample> getNegatives(List<Sample> ex) {
        List<Sample> negatives = new ArrayList<>();
        for (Sample e : ex) {
            if (e.getExample().getExpectedValue() == 0) {
                negatives.add(e);
            }
        }
        return negatives;
    }

    public boolean hasNext() {
        return testFold < foldCount;
    }

    public void next() {
        testFold++;
    }

    public List<Sample> getTrain() {
        List<Sample> tmp = new ArrayList<Sample>();
        int i = 0;
        for (List<Sample> fold : folds) {
            if (i++ != testFold || (foldCount == 1 && testFold != 1)) {    //or just a training set (that shouldnt cause anything in crossval)
                tmp.addAll(fold);
            }
        }

        Collections.shuffle(tmp, Global.getRg());
        return tmp;
    }

    public List<Sample> getTest() {
        return folds.get(testFold);
    }

    private void numberSamples(List<Sample> ex) {
        if (Global.isOutputFolds()) {
            Glogger.debug("---------------------------whole sample set------------------------------");
        }
        for (int i = 0; i < ex.size(); i++) {
            ex.get(i).position = i;
            if (Global.isOutputFolds()) {
                Glogger.debug("sample " + i + " : " + ex.get(i).toString());
            }
        }
    }

    public static List<List<Example>> splitExampleList(List<Example> examples1, int folds) {
        List<List<Example>> workFolds = new LinkedList<>();
        for (int i = 0; i < folds; i++) {
            workFolds.add(new LinkedList<>());
        }
        for (int i = 0; i < examples1.size(); i++) {
            workFolds.get(i % folds).add(examples1.get(i));
        }
        return workFolds;
    }

    public static List<List<Sample>> splitSampleList(List<Sample> examples1, int folds) {
        List<List<Sample>> workFolds = new LinkedList<>();
        for (int i = 0; i < folds; i++) {
            workFolds.add(new LinkedList<>());
        }
        for (int i = 0; i < examples1.size(); i++) {
            workFolds.get(i % folds).add(examples1.get(i));
        }
        return workFolds;
    }
}
