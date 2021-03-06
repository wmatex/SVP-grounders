/*
 * To change this license header, choose License Headers in Project Properties.
 * To change this template file, choose Tools | Templates
 * and open the template in the editor.
 */
package lrnn.construction.template;

import lrnn.construction.template.rules.KappaRule;
import lrnn.construction.template.rules.Rule;
import lrnn.construction.template.rules.SubK;
import lrnn.global.Global;
import lrnn.grounding.network.GroundKL;
import lrnn.grounding.network.groundNetwork.GroundNetwork;
import lrnn.grounding.network.groundNetwork.GroundNeuron;
import lrnn.learning.Saver;

import javax.swing.*;
import java.io.*;
import java.util.*;
import java.util.logging.Level;
import java.util.logging.Logger;

/**
 * A placeholder for the whole network and affiliated functions the network
 * itself is otherwise treated recursively by the last/final KL node
 *
 * @author Gusta
 */
public class LiftedTemplate extends LightTemplate implements Serializable {

    public LinkedHashSet<Rule> rules = new LinkedHashSet<>();   //=for network input/output file
    protected Set<Kappa> kappas = new HashSet<>();
    private HashSet<Lambda> lambdas = new HashSet<>();
    public Map<Integer, String> constantNames;

    //------------
    public HashMap<String, Integer> weightMapping;  //Kappa offsets and KappaRule's weights to indicies in sharedWeights

    public HashMap<GroundKL, GroundNeuron> neuronMapping; //for checking if we have already visited this groundKL?

    //------------
    public GroundNetwork tmpActiveNet; //auxiliary to get reference from neurons to their mother network (without storing pointer in them cause of serialization)

    public KL last;

    LinkedList<KL> queue = new LinkedList<>();

    /*PriorityQueue<KL> queueSorted = new PriorityQueue<KL>(new Comparator<KL>() { //tmp for BFS
     public int compare(KL kl1, KL kl2) {
     return (kl1.toString().compareToIgnoreCase(kl2.toString()));    //lexicograhpical ordering
     }
     });*/
    public LiftedTemplate() {
    }

    public LiftedTemplate(double[] sharedW, HashMap<String, Integer> name2weights) {
        sharedWeights = sharedW;
        name2weight = name2weights;
    }

    public LiftedTemplate(KL kl) {
        last = kl;
        queue.add(kl);

        (new File(weightFolder)).mkdirs();

        while (!queue.isEmpty()) {
            KL first = queue.remove();
            if (first instanceof Kappa) {
                this.getRules((Kappa) first);
            } else {
                getRules((Lambda) first);
            }
        }
    }

    public static LiftedTemplate loadNetwork() {
        File file = null;
        LiftedTemplate network = null;

        if (Global.isGUI()) {
            JFrame jf = new JFrame();
            JFileChooser fileChooser = new JFileChooser();
            if (fileChooser.showOpenDialog(jf) == JFileChooser.APPROVE_OPTION) {
                file = fileChooser.getSelectedFile();
            }
        } else {
            file = new File(Global.outputFolder + "networkObject");
        }

        try {
            FileInputStream fos = new FileInputStream(file.getAbsoluteFile());
            ObjectInputStream save = new ObjectInputStream(fos);
            network = (LiftedTemplate) save.readObject();
            save.close();
        } catch (FileNotFoundException ex) {
            Logger.getLogger(Saver.class.getName()).log(Level.SEVERE, null, ex);
        } catch (IOException ex) {
            Logger.getLogger(Saver.class.getName()).log(Level.SEVERE, null, ex);
        } catch (ClassNotFoundException ex) {
            Logger.getLogger(Saver.class.getName()).log(Level.SEVERE, null, ex);
        }
        return network;
    }

    private void getRules(Kappa k) {
        getKappas().add(k);
        for (KappaRule kr : k.getRules()) {
            Lambda lam = kr.getBody().getParent();
            queue.add(lam);
            if (rules.contains(kr)) {
                return;
            }
            rules.add(kr);
        }
    }

    private void getRules(Lambda l) {
        getLambdas().add(l);
        if (l.getRule() == null) {
            return;
        }
        if (rules.contains(l.getRule())) {
            return;
        }
        rules.add(l.getRule());
        for (SubK sk : l.getRule().getBody()) {
            queue.add(sk.getParent());
        }
    }

    void exportOffsets(BufferedWriter test, String name) throws IOException, FileNotFoundException, UnsupportedEncodingException {
        if (getKappas().isEmpty()) {
            return;
        }
        LinkedList<String> kapString = new LinkedList<>();
        //test = new BufferedWriter(new OutputStreamWriter(new FileOutputStream(outputFolder + name + "-offsets.w"), "utf-8"));

        for (Kappa kap : getKappas()) {
            kapString.add(kap.name + " " + kap.getOffset() + "\n");
        }
        Collections.sort(kapString);
        for (String ks : kapString) {
            test.write(ks);
        }
        test.close();
    }

    @Override
    public void exportTemplate(String name) {
        if (rules.isEmpty()) {
            super.exportTemplate(name);
            return;
        }
        BufferedWriter test = null;
        StringBuilder sb = new StringBuilder();
        try {
            test = new BufferedWriter(new OutputStreamWriter(new FileOutputStream(weightFolder + name + ".txt"), "utf-8"));
            ArrayList<Rule> rulzz = new ArrayList(rules);
            for (int i = rulzz.size() - 1; i >= 0; i--) {
                sb.append(rulzz.get(i).toFullString()).append("\n");
            }
            test.write(sb.toString());

            exportOffsets(test, name);
            test.close();
        } catch (UnsupportedEncodingException ex) {
            Logger.getLogger(Saver.class.getName()).log(Level.SEVERE, null, ex);
        } catch (IOException ex) {
            Logger.getLogger(Saver.class.getName()).log(Level.SEVERE, null, ex);
        } finally {
            try {
                test.close();
            } catch (IOException ex) {
                Logger.getLogger(Saver.class.getName()).log(Level.SEVERE, null, ex);
            }
        }
    }

    /**
     * @return the kappas
     */
    public Set<Kappa> getKappas() {
        return kappas;
    }

    /**
     * @param kappas the kappas to set
     */
    public void setKappas(HashSet<Kappa> kappas) {
        this.kappas = kappas;
    }

    /**
     * @return the lambdas
     */
    public HashSet<Lambda> getLambdas() {
        return lambdas;
    }

    /**
     * @param lambdas the lambdas to set
     */
    public void setLambdas(HashSet<Lambda> lambdas) {
        this.lambdas = lambdas;
    }

    /**
     * backwards mapping of learned weights to template's rules
     *
     * @param weightMapping
     * @param sharedWeights
     * @return
     */
    public boolean setWeightsFromArray(HashMap<String, Integer> weightMapping, double[] sharedWeights) {
        Integer idx;
        for (Rule rule : rules) {
            if (rule instanceof KappaRule) {
                KappaRule kr = (KappaRule) rule;
                if ((idx = weightMapping.get(kr.toString())) != null) {
                    //System.out.println(kr + " : " + kr.getWeight() + " -> " + sharedWeights[idx]);
                    kr.setWeight(sharedWeights[idx]);
                }
            }
        }
        for (Kappa kappa : getKappas()) {
            if ((idx = weightMapping.get(kappa.toString())) != null) {
                kappa.setOffset(sharedWeights[idx]);
            }
        }
        return true;
    }
}
