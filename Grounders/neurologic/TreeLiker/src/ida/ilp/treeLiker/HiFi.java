/*
 * To change this template, choose Tools | Templates
 * and open the template in the editor.
 */

package ida.ilp.treeLiker;

import ida.ilp.treeLiker.aggregables.VoidAggregablesBuilder;
import ida.ilp.treeLiker.impl.*;
import ida.utils.Sugar;
import ida.utils.collections.MultiList;
import ida.utils.collections.MultiMap;
import ida.utils.tuples.Pair;

import java.util.*;
import java.util.concurrent.ConcurrentHashMap;

/**
 * Class implementing algorithm HiFi (Kuzelka, Zelezny, ILP - late breaking papers, 2008).
 * 
 * @author Ondra
 */
public class HiFi {

    private List<ProgressListener> progressListeners = new ArrayList<ProgressListener>();

    private Dataset examples;

    private int maxSize = Integer.MAX_VALUE;
    
    private int maxAggregators = Integer.MAX_VALUE;
    
    private int[] mask;

    private boolean alive = true;

    protected static int LITERALS = 1, TERMS = 2;
    
    private HSubsumption hsubsumptionEngine = new HSubsumption();
    
    private DomainComputing domainComputing;
    
    private Pruning pruning;
    
    private List<SyntaxChecker> syntaxCheckers = new ArrayList<SyntaxChecker>();
    
    private AggregablesBuilder aggregablesBuilder = VoidAggregablesBuilder.construct();
    
    private AggregablesBuilder postProcessingAggregablesBuilder = VoidAggregablesBuilder.construct();
    
    private Block normalizationFactor;

    /**
     * Creates a new instance of class HiFi.
     * @param examples datset of examples for which features should be constructed or for which propositionalized table should be constructed.
     */
    public HiFi(Dataset examples){
        this.examples = examples;
        this.domainComputing = new DomainComputing(this.examples.shallowCopy());
        this.mask = new int[examples.countExamples()];
        Arrays.fill(this.mask, Consts.POSITIVE);
        this.pruning = new Pruning(mask, 1);
    }

    /**
     * Constructs all non-reducible non-redundant features complying with the language bias
     * specified using set <em>definitions</em>
     * @param definitions templates - i.e. specification of language bias (similar to mode declarations)
     * @return List of constructed features
     */
    public List<Block> constructFeatures(Set<PredicateDefinition> definitions){
        if (!alive){
            throw new IllegalStateException("Each instance of class RelF can be used only once.");
        } else {
            alive = false;
        }
        List<Block> constructedFeatures = new ArrayList<Block>();
        MultiList<Integer, Block> mm = new MultiList<Integer, Block>();
        List<PredicateDefinition> open = buildOpenList(definitions);
        this.syntaxCheckers.add(new MaxSizeChecker(this.maxSize, open));
        this.syntaxCheckers.add(new NumAggregatorsChecker(this.maxAggregators));
        for (ProgressListener pl : progressListeners) {
            pl.readingExamples();
        }
        List<PredicateDefinition> inputOnlyDefinitions = new ArrayList<PredicateDefinition>();
        for (PredicateDefinition def : open){
            if (def.isInputOnly()){
                inputOnlyDefinitions.add(def);
            }
        }
        open = Sugar.listDifference(open, inputOnlyDefinitions);
        for (PredicateDefinition def : inputOnlyDefinitions){
            if (Settings.VERBOSITY > 0){
                System.out.println("Processing: " + def);
            }
            for (ProgressListener pl : this.progressListeners){
                pl.processingPredicate(def);
            }
            if (def.isInputOnly()) {
                List<Block> generatedPosFeatures = new ArrayList<Block>();
                Block posFeat = new Block(def, this.aggregablesBuilder);
                int[] modes = def.modes();
                for (int j = 0; j < modes.length; j++) {
                    if (modes[j] == PredicateDefinition.INPUT){
                        generatedPosFeatures.add(posFeat);
                    }
                }
                mm.putAll(def.types()[def.input()], generatedPosFeatures);
            }
        }
        for (Map.Entry<Integer,List<Block>> entry : mm.copy().entrySet()){
            Map<Integer, Domain[]> computedDomains = domainComputing.computeTermDomainsInParallel(entry.getValue());
            Collection<Block> filtered = pruning.filterRedundantBlocksInParallel(entry.getValue(), computedDomains);
            mm.set(entry.getKey(), filtered);
        }
        examples.reset();
        for (int i = 0; i < open.size(); i++) {
            PredicateDefinition def = open.get(i);
            if (Settings.VERBOSITY > 0){
                System.out.println("Processing: " + def);
            }
            for (ProgressListener pl : this.progressListeners){
                pl.processingPredicate(def);
            }
            List<Collection<Join>> combinations = Collections.synchronizedList(new ArrayList<Collection<Join>>());
            for (int j = 0; j < def.modes().length; j++) {
                if (def.modes()[j] == PredicateDefinition.OUTPUT) {
                    combinations.add(combinationsOfPosFeatures(mm, def.types()[j], def.branchingFactors()[j]));
                } else {
                    combinations.add(new ArrayList<Join>());
                }
            }
            Collection<Block> newBlocks = buildBlocksFromCombinations(def, combinations);
            if (def.isOutputOnly()){
                for (Block newFeature : newBlocks){
                    constructedFeatures.add(newFeature);
                }
            } else {
                if (mm.containsKey(def.types()[def.input()])){
                    Map<Integer, Domain[]> computedDomains = domainComputing.computeTermDomainsInParallel(Sugar.listFromCollections(newBlocks, mm.get(def.types()[def.input()])));
                    Collection<Block> filtered = pruning.filterRedundantBlocksInParallel(Sugar.setFromCollections(newBlocks, mm.get(def.types()[def.input()])), computedDomains);
                    mm.set(def.types()[def.input()], filtered);
                } else {
                    mm.putAll(def.types()[def.input()], newBlocks);
                }
            }
        }
        return constructedFeatures;
    }
    
    /**
     * Given a set of features (instances of class Block), this method computes the propositionalized table.
     * @param constructedFeatures set of constructed features
     * @return propositionalized table (i.e. an attribute-value table) iterable which the features play the role of attributes.
     */
    public Table<Integer,String> constructTable(List<Block> constructedFeatures){
        examples.reset();
        Table<Integer,String> table = new Table<Integer,String>();
        while (examples.hasNextExample()){
            examples.nextExample();
            table.addClassification(examples.currentIndex(), examples.classificationOfCurrentExample());
        }
        Map<Integer,Domain[]> domains = domainComputing.computeLiteralDomainsInParallel(constructedFeatures);
        if (this.postProcessingAggregablesBuilder != null && !this.aggregablesBuilder.equals(this.postProcessingAggregablesBuilder) && !(this.postProcessingAggregablesBuilder instanceof VoidAggregablesBuilder)){
            FeaturesProcessing.process(constructedFeatures, new Sugar.VoidFun<Block>(){
                public void apply(Block t) {
                    t.deleteCachedDomains();
                    t.setAggregablesBuilder(postProcessingAggregablesBuilder);
                }
            });
        }
        if (this.normalizationFactor != null){
            this.normalizationFactor.applyRecursively(new Sugar.Fun<Block,Block>(){
                public Block apply(Block t) {
                    t.setAggregablesBuilder(postProcessingAggregablesBuilder);
                    return t;
                }
            });
        }
        examples.reset();
        while (examples.hasNextExample()) {
            Example example = examples.nextExample();
            Double normalizationCoeff = null;
            if (this.normalizationFactor != null){
                Domain d = this.normalizationFactor.termDomain(-1, example);
                if (!d.isEmpty() && d.getAggregableByDomainElement(-1) != null){
                    normalizationCoeff = new Double(d.getAggregableByDomainElement(-1).toString());
                }
            }
            for (Block block : constructedFeatures){
                if (this.aggregablesBuilder instanceof VoidAggregablesBuilder && this.postProcessingAggregablesBuilder instanceof VoidAggregablesBuilder){
                    if (!block.literalDomain(example).isEmpty()){
                        table.add(examples.currentIndex(), block.toClause(), "+", block.size());
                    } else {
                        table.add(examples.currentIndex(), block.toClause(), "-", block.size());
                    }
                } else {
                    if (!domains.get(block.id())[examples.currentIndex()].isEmpty()){
                        Domain domain = block.termDomain(-1, example);
                        if (normalizationCoeff == null){
                            table.add(examples.currentIndex(), block.toClause(), domain.getAggregableByDomainElement(-1).toString()); 
                        } else {
                            table.add(examples.currentIndex(), block.toClause(), String.valueOf(Double.parseDouble(domain.getAggregableByDomainElement(-1).toString())/normalizationCoeff)); 
                        }
                    } else {
                        table.add(examples.currentIndex(), block.toClause(), "0", block.size());
                    }
                }
            }
        }
        for (ProgressListener pl : progressListeners) {
            pl.finished(table.countOfAttributes());
        }
        return table;
    }

    private Collection<Join> combinationsOfPosFeatures(MultiList posFeatures, int inputType, int branching){
        //[example,term] -> [pos feature, which has term iterable its domain]
        MultiMap<Pair<Integer,Integer>,Block> termsInDomainsOf = new MultiMap<Pair<Integer,Integer>,Block>();
        List<Block> listOfBlocks = Sugar.listFromCollections(posFeatures.get(inputType));
        ConcurrentHashMap<Block,Integer> indices = new ConcurrentHashMap<Block,Integer>();
        ConcurrentHashMap<Integer,Block> posFeaturesLookup = new ConcurrentHashMap<Integer,Block>();
        for (int i = 0; i < listOfBlocks.size(); i++){
            indices.put(listOfBlocks.get(i), i);
            posFeaturesLookup.put(listOfBlocks.get(i).id(), listOfBlocks.get(i));
        }
        ConcurrentHashMap<Integer,Domain[]> computedDomainsOfBlocks = domainComputing.computeTermDomainsInParallel(listOfBlocks);
        List<TermsInDomainsOfBuilder> tasks0 = new ArrayList<TermsInDomainsOfBuilder>();
        for (Map<Integer,Domain[]> taskMap : Sugar.splitMap(computedDomainsOfBlocks, Settings.PROCESSORS)){
            tasks0.add(new TermsInDomainsOfBuilder(termsInDomainsOf, taskMap, posFeaturesLookup, mask));
        }
        Sugar.runInParallel(tasks0);
        //[number of pos features iterable combination] -> [combination of pos features, index of the last pos feature iterable the combination]
        MultiList<Integer,JoinAndInt> hbl = new MultiList<Integer,JoinAndInt>();
        ConcurrentHashMap<Pair<Block,Block>,Boolean> hSubsumptions = new ConcurrentHashMap<Pair<Block,Block>,Boolean>();
        ConcurrentHashMap<List<Domain>,Integer> redundancyMap = new ConcurrentHashMap<List<Domain>,Integer>();
        for (int i = 0; i < listOfBlocks.size(); i++){
            hbl.put(1, new JoinAndInt(new Join(listOfBlocks.get(i)), i));
        }
        for (int i = 1; i < branching; i++){
            List<CombinationsBuilder> tasks1 = Collections.synchronizedList(new ArrayList<CombinationsBuilder>());
            for (JoinAndInt tuplePair : hbl.get(i)){
                //suspicious - maybe race condition - check later!!!!
                if (tuplePair != null){
                    tasks1.add(new CombinationsBuilder(tuplePair, redundancyMap, indices, hSubsumptions, hbl, i, termsInDomainsOf, domainComputing, hsubsumptionEngine, pruning, syntaxCheckers));
                }
            }
            Sugar.runInParallel(tasks1, Settings.PROCESSORS);
            for (CombinationsBuilder cb : tasks1){
                redundancyMap.putAll(cb.getRedundancyMap());
            }
            if (hbl.get(i+1).isEmpty()){
                break;
            }
            Collection<JoinAndInt> filtered = hbl.get(i+1);
            hbl.set(i+1, filtered);
        }
        List<JoinAndInt> flattened = Collections.synchronizedList(new ArrayList<JoinAndInt>());
        for (Map.Entry<Integer, List<JoinAndInt>> entry : hbl.entrySet()){
            for (JoinAndInt pair : entry.getValue()){
                flattened.add(pair);
            }
        }
        List<Join> retVal = Collections.synchronizedList(new ArrayList<Join>());
        for (JoinAndInt pair : flattened){
            if (pair != null){
                retVal.add(pair.r);
            }
        }
        return retVal;
    }

    private Collection<Block> buildBlocksFromCombinations(PredicateDefinition def, List<Collection<Join>> combinations){
        //[argument,literal's] id (iterable domain of pos feature F) -> pos feature F
        MultiMap<Pair<Integer,Integer>,Join> bagPosFeaturesWithLiteralsInDomain = new MultiMap<Pair<Integer,Integer>,Join>();
        int argument = 0;
        for (Collection<Join> list : combinations){
            List<BlocksWithLiteralsInDomainBuilder> tasks0 = new ArrayList<BlocksWithLiteralsInDomainBuilder>();
            for (Join join : list){
                tasks0.add(new BlocksWithLiteralsInDomainBuilder(join, def.predicate(), argument, bagPosFeaturesWithLiteralsInDomain, this.examples));
            }
            Sugar.runInParallel(tasks0, Settings.PROCESSORS);
            argument++;
        }
        Block root = new Block(def, this.aggregablesBuilder);
        List<Block> old = Sugar.<Block>list(root);
        List<Block> current = Collections.synchronizedList(new ArrayList<Block>());
        ConcurrentHashMap<Integer,Domain[]> domains = new ConcurrentHashMap<Integer,Domain[]>();
        domains.put(root.id(), domainComputing.computeLiteralDomains(root));
        for (int arg = 0; arg < def.modes().length; arg++){
            if (def.modes()[arg] == PredicateDefinition.OUTPUT){
                List<BlockBuilder> tasks1 = new ArrayList<BlockBuilder>();
                for (Block oldPos : old){
                    tasks1.add(new BlockBuilder(oldPos, arg, bagPosFeaturesWithLiteralsInDomain, domains, current, domainComputing, pruning, this.syntaxCheckers));
                }
                Sugar.runInParallel(tasks1, Settings.PROCESSORS);
                current = Sugar.listFromCollections(pruning.filterRedundantBlocksInParallel(current, domains));
                old = current;
                current = Collections.synchronizedList(new ArrayList<Block>());
            }
        }
        return old;
    }

    /**
     * Sets minimum frequency of features.
     * @param minFreq absolute minimum-frequency (i.e. not relative minimum frequency represented as percentage or something similar)
     */
    public void setMinFrequency(int minFreq){
        this.pruning.setMinFrequencyOnCoveredClass(minFreq);
    }

    private static List<PredicateDefinition> buildOpenList(Collection<PredicateDefinition> defs){
        return FeatureSearchUtils.buildPredicateList(defs);
    }

    /**
     * Adds progress listeners
     * @param pl progress listener
     */
    public void addProgressListener(ProgressListener pl) {
        progressListeners.add(pl);
    }
    
    /**
     * Adds syntax checker. Syntax checkers are used to constrain the form of Blocks,
     * for example it is possible to have MaxSizeChecker, which efficiently checks if
     * a given block can be extended to a full feature (complying to the language bias)
     * with size at most a given limit (note that this problem is NP-hard for non-tree-like features - see (Kuzelka, 2009 - Master's thesis).
     * However, this MaxSizeChecker is used by default by HiFi so it is not neccessary to set it explicitly - but still, it
     * is possible to have some custom syntax checkers.
     * 
     * @param syntaxChecker the syntax checker
     */
    public void addSyntaxChecker(SyntaxChecker syntaxChecker){
        this.syntaxCheckers.add(syntaxChecker);
    }

    /**
     * Sets the maximum allowed size of features to be constructed.
     * @param maxSize the maxSize
     */
    public void setMaxSize(int maxSize) {
        this.maxSize = maxSize;
    }

    /**
     * Sets the AggregablesBuilder which is used to bguild Aggregables which are 
     * objects used for various aggregation tasks or extraction tasks etc.
     * 
     * @param aggregablesBuilder the aggregablesBuilder to set
     */
    public void setAggregablesBuilder(AggregablesBuilder aggregablesBuilder) {
        this.aggregablesBuilder = aggregablesBuilder;
    }

    /**
     * It is possible to use different variableTypes of aggregables for construction of features and for construction
     * of tables - the latter aggregables are called post-processing aggregables. This possibility may be useful
     * for example when computing aggregables is computationally costly.
     * 
     * @param postProcessingAggregablesBuilder the postProcessingAggregablesBuilder
     */
    public void setPostProcessingAggregablesBuilder(AggregablesBuilder postProcessingAggregablesBuilder) {
        this.postProcessingAggregablesBuilder = postProcessingAggregablesBuilder;
    }

    /**
     * Sets the maximum number of aggregation-variables which can appear iterable a block - this
     * may be helpful iterable that it allows reducing the space of possible features.
     * 
     * @param maxAggregators the maximum number of aggregation variables
     */
    public void setMaxAggregators(int maxAggregators) {
        this.maxAggregators = maxAggregators;
    }

    /**
     * Sets the normalization block - normalization block is used for normalizing 
     * results of aggregation - aggregated values of features is divided by aggregated value of the <em>normalizationFactor</em>
     * @param normalizationFactor the normalizationFactor 
     */ 
    public void setNormalizationFactor(Block normalizationFactor) {
        this.normalizationFactor = normalizationFactor;
    }
}
