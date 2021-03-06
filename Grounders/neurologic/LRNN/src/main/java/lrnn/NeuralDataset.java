/*
 * To change this license header, choose License Headers in Project Properties.
 * To change this template file, choose Tools | Templates
 * and open the template in the editor.
 */
package lrnn;

import lrnn.construction.template.Kappa;
import lrnn.construction.template.LiftedTemplate;
import lrnn.construction.template.MolecularTemplate;
import lrnn.construction.template.rules.KappaRule;
import lrnn.construction.template.rules.Rule;
import lrnn.drawing.GroundDotter;
import lrnn.global.Global;
import lrnn.grounding.network.groundNetwork.GroundNetwork;
import lrnn.grounding.network.groundNetwork.GroundNeuron;
import lrnn.learning.Sample;

import java.io.Serializable;
import java.util.*;

/**
 * This is a lightweight dataset representation - this class contains only all
 * the things necessary for learning phase - for memory saving and speedup
 */
public class NeuralDataset extends LiftedDataset implements Serializable {

    //this SampleSplitter contains small samples (low memory) as they do not contain Example and GroundTemplate (K/L) structures
    //public SampleSplitter sampleSplitter;  //those samples contain only groundNetworks (the same objects as bellow) and their target values
    //public GroundNetwork[] groundNetworks;
    public long timeToBuild;

    public NeuralDataset(LiftedDataset ld) {
        //super();  //copy necessary input network's variables
        //network = ld.network;

        pretrained = ld.pretrained;
        sampleSplitter = ld.sampleSplitter;

        LiftedTemplate net = ld.template;

        net.weightMapping = new HashMap<>(net.rules.size());
        net.neuronMapping = new HashMap<>(net.rules.size());
        createSharedWeights(net);

        makeNeuralNetworks(net, sampleSplitter.samples);

        makeTemplate(net);
    }

    /**
     * sets the Lifted Network template from previous LitedDataset or creates a
     * new lightweight version of it
     *
     * @param template
     */
    public final void makeTemplate(LiftedTemplate template) {
        //makeMeSmall(network);
        template.name2weight = new LinkedHashMap<>(template.rules.size());
        for (Map.Entry<String, Integer> woi : template.weightMapping.entrySet()) {
            template.name2weight.put(woi.getKey(), woi.getValue());
        }
        if (Global.memoryLight) {
            super.template = new LiftedTemplate(template.sharedWeights, template.name2weight);
        } else {
            super.template = template;
        }
    }

    /**
     * mapping of lifted template weights into the sharedWeights vector
     *
     * @param network
     */
    final void createSharedWeights(LiftedTemplate network) {
        int weightCounter = 0;
        List<Boolean> learnable = new ArrayList<>();
        for (Rule rule : network.rules) {
            if (rule instanceof KappaRule) {
                network.weightMapping.put(((KappaRule) rule).toString(), weightCounter++);
                learnable.add(((KappaRule) rule).learnableWeight);
            }
        }
        for (Kappa kappa : network.getKappas()) {
            //if (!kappa.getRules().isEmpty()) {    // - nope, let's learn Kappa elements offsets too in the fast version! :)
            network.weightMapping.put(kappa.toString(), weightCounter++);
            learnable.add(kappa.hasLearnableOffset);
            //}
        }
        network.sharedWeights = new double[weightCounter];
        network.isLearnable = new boolean[weightCounter];
        for (int i = 0; i < weightCounter; i++) {
            network.isLearnable[i] = learnable.get(i);
        }
    }

    /**
     * creation of the fast neural network objects
     *
     * @param net
     * @param samples
     */
    public final void makeNeuralNetworks(LiftedTemplate net, List<Sample> samples) {
        //Global.neuralDataset = this; //important here - not anymore
        //groundNetworks = new GroundNetwork[samples.size()];
        for (int i = 0; i < samples.size(); i++) {
            Sample sample = samples.get(i);
            if (sample.getBall().getLast() != null) {
                sample.neuralNetwork = new GroundNetwork();
                sample.neuralNetwork.allNeurons = new GroundNeuron[sample.getBall().groundLiterals.size()];  //only higher layer (no-fact) neurons!
                net.tmpActiveNet = sample.neuralNetwork;
                net.constantNames = sample.getBall().constantNames;
                sample.neuralNetwork.createNetwork(sample, net);
            }
            sample.targetValue = sample.getExample().getExpectedValue();

            //GroundDotter.drawAVG(sample.getBall(),"testNormal");
            if (Global.drawing) {
                GroundDotter.drawNeural(sample.neuralNetwork, "testNeural"+i, net.sharedWeights);
            }
            if (Global.memoryLight) {
                sample.makeMeSmall();   //make the sample small!
            }
        }
    }

    /**
     * clear unnecessary structures for learning
     *
     * @param network
     */
    public final void makeMeSmall(MolecularTemplate network) {
        network.tmpActiveNet = null;
        network.neuronMapping = null;
        network.weightMapping = null;
    }
}
