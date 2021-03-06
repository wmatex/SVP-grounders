/*
 * To change this license header, choose License Headers in Project Properties.
 * To change this pretrainedTemplate file, choose Tools | Templates
 * and open the pretrainedTemplate in the editor.
 */
package lrnn;

import lrnn.construction.ExampleFactory;
import lrnn.construction.TemplateFactory;
import lrnn.construction.example.Example;
import lrnn.construction.template.LiftedTemplate;
import lrnn.construction.template.LightTemplate;
import lrnn.crossvalidation.SampleSplitter;
import lrnn.drawing.Dotter;
import lrnn.global.Global;
import lrnn.global.Glogger;
import lrnn.learning.Sample;

import java.io.*;
import java.util.ArrayList;
import java.util.List;

/**
 * Abstraction of a dataset of the level of original template(rules) - contains
 * high level structures and features - e.g. template creation, merging, saving
 * and loading
 */
public class LiftedDataset implements Serializable {

    TemplateFactory nf;

    public LiftedTemplate template;

    String[] pretrained = null;
    public LightTemplate pretrainedTemplate = null;

    public SampleSplitter sampleSplitter;

    public LiftedDataset() {
    }

    //public HashMap<Object, Integer> weightMapping;  //Kappa offsets and KappaRule's weights to indicies in sharedWeights
    //public double[] sharedWeights; //the shared sharedWeights
    public LiftedDataset(String[] rules, String[] PretrainedRules) {
        pretrained = PretrainedRules;
        template = createNetworkMerge(rules);

        //createSharedWeights();
    }

    public LiftedTemplate createNetworkMerge(String[] rules) {
        LiftedTemplate pretrainedN = null;
        if (pretrained != null && pretrained.length > 0) {
            pretrainedN = createNetwork(pretrained, "pretrained"); // 1st
        }

        LiftedTemplate net = createNetwork(rules, "network"); // 2nd

        if (Global.getMerging() == Global.mergingOptions.weights) {
            net.merge(pretrainedN); // 3rd
            Glogger.process("merged weights with template of : " + pretrainedN);
        }
        if (Global.getMerging() == Global.mergingOptions.onTop) {
            net = net.mergeOnTop(pretrainedN); // 3rd
            Glogger.process("merged structures on top (side by side) with template of : " + pretrainedN);
        }

        if (Global.drawing) {
            Dotter.draw(net.last);
        }

        if (Global.exporting && Global.getMerging() != null) {
            net.exportTemplate("merged");
            net.exportWeightMatrix("merged");
        }

        template = net;
        pretrainedTemplate = pretrainedN;

        return net;
    }

    public final LiftedTemplate createNetwork(String[] rules, String name) {
        //factory + subfactories initialization
        nf = null;
        //constructs the whole L-K network from rules with support of grounded classes and element mappers, return LAST line rule's literal(=KL)!
        LiftedTemplate template = null;

        if (rules.length == 0) {
            Glogger.out("network template -" + name + "- is empty, may try to load manually if GUI is on...");
            if (Global.isLoadLiftedNetworkObject()) {
                template = LiftedTemplate.loadNetwork();
                return template;
            }
            return null;
        }

        nf = new TemplateFactory();
        template = nf.construct(rules);

        if (Global.exporting) {
            template.exportTemplate(name);
            template.exportWeightMatrix(name);
        }
        return template;
    }

    /**
     * creates shuffled list of Examples from descriptions(conjunction of
     * literals)
     *
     * @param ex
     * @param maxExamples
     * @return
     */
    public final List<Example> createExamples(String[] ex, int maxExamples) {
        ExampleFactory eFactory = new ExampleFactory();
        List<Example> examples = new ArrayList<>();
        int positives = 0;
        int negatives = 0;
        for (int i = 0; i < ex.length; i++) {
            //main creation of an example
            Example e = eFactory.construct(ex[i]);
            examples.add(e);
            if (e.getExpectedValue() > 0) {
                positives++;
            } else {
                negatives++;
            }
        }
        /*
        if (Global.shuffleExamples) {
            Collections.shuffle(examples, Global.getRg());
        }
        */

        if (maxExamples > examples.size()) {
            return examples;
        }
        //stratified decreasing the number of examples
        positives = (int) Math.round(1.0 * positives / (examples.size()) * maxExamples);
        negatives = (int) Math.round(1.0 * negatives / (examples.size()) * maxExamples);
        List<Example> finExamples = new ArrayList<>();

        for (Example e : examples) {
            if (e.getExpectedValue() > 0) {
                positives--;
                if (positives >= 0) {
                    finExamples.add(e);
                }
            } else {
                negatives--;
                if (negatives >= 0) {
                    finExamples.add(e);
                }
            }
        }
        return finExamples;
    }

    public boolean saveDataset(String path) {
        try {
            Glogger.process("Saving grounded dataset...");
            FileOutputStream out = new FileOutputStream(path);
            ObjectOutputStream oos = new ObjectOutputStream(out);
            oos.writeObject(this);
            oos.flush();
            Glogger.process("Successfully Saved grounded dataset into: " + path);
            return true;
        } catch (Exception e) {
            Glogger.err("Problem serializing: " + e);
            return false;
        }
    }

    public static LiftedDataset loadDataset(String path) {
        LiftedDataset sampleStore = null;
        try {
            Glogger.process("trying to load grounded dataset from a file: " + path);
            FileInputStream in = new FileInputStream(path);
            ObjectInputStream ois = new ObjectInputStream(in);
            sampleStore = (LiftedDataset) (ois.readObject());
            Glogger.process("grounded network examples succesfully loaded from : " + path + ".ser");
        } catch (IOException | ClassNotFoundException e) {
            Glogger.info("Problem loading grounded dataset: " + e);
            Glogger.info("-> Will try to ground the dataset as ussual instead");
        }
        return sampleStore;
    }

    public boolean saveSampleSet(String path, List<Sample> sampleSet) {
        try {
            Glogger.process("Saving grounded dataset...");
            FileOutputStream out = new FileOutputStream(path);
            ObjectOutputStream oos = new ObjectOutputStream(out);
            oos.writeObject(sampleSet);
            oos.flush();
            Glogger.process("Successfully Saved grounded dataset into: " + path);
            return true;
        } catch (Exception e) {
            Glogger.err("Problem serializing: " + e);
            return false;
        }
    }
}
