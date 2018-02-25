/*
 * To change this template, choose Tools | Templates
 * and open the template in the editor.
 */
package ida.ilp.treeLiker.impl;

import ida.ilp.treeLiker.Block;
import ida.ilp.treeLiker.Join;
import ida.ilp.treeLiker.SyntaxChecker;

/**
 * Class implementing methods for checking if a sub-block does not have greater-than-allowed
 * number of aggregation variables.
 * 
 * @author Ondra
 */
public class NumAggregatorsChecker implements SyntaxChecker {

    private int max;
    
    /**
     * Creates a new instance of class NumAggregatorsChecker
     * @param max maximum allowed number of aggregation variables
     */
    public NumAggregatorsChecker(int max){
        this.max = max;
    }
    
    public boolean check(Block block) {
        return block.numAggregators() <= max;
    }

    public boolean check(Join join) {
        return join.numAggregators() <= max;
    }
}
