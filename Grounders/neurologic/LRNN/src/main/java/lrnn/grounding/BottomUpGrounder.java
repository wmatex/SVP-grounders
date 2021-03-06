package lrnn.grounding;

import ida.ilp.logic.Clause;
import ida.ilp.logic.Literal;
import ida.ilp.logic.LogicUtils;
import ida.ilp.logic.Term;
import ida.ilp.logic.subsumption.CustomPredicate;
import ida.ilp.logic.subsumption.Matching;
import ida.ilp.logic.subsumption.SolutionConsumer;
import ida.utils.Sugar;
import ida.utils.VectorUtils;
import ida.utils.collections.MultiMap;
import ida.utils.tuples.Pair;
import lrnn.global.Glogger;

import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

/**
 * Created by ondrejkuzelka on 11/06/16.
 */
public class BottomUpGrounder {

    public Set<Literal> herbrandModel(List<? extends Clause> clauses) {
        MultiMap<Pair<String, Integer>, Literal> herbrand = new MultiMap<Pair<String, Integer>, Literal>();
        Pair<List<Clause>, List<Literal>> rulesAndFacts = rulesAndFacts(clauses);
        List<Clause> rules = rulesAndFacts.r;
        for (Literal groundLiteral : rulesAndFacts.s) {
            herbrand.put(new Pair<String, Integer>(groundLiteral.predicate(), groundLiteral.arity()), groundLiteral);
        }

        Set<Pair<String, Integer>> headSignatures = new HashSet<Pair<String, Integer>>();
        for (Clause rule : rules) {
            Literal head = head(rule);
            Pair<String, Integer> headSignature = new Pair<String, Integer>(head.predicate(), head.arity());
            headSignatures.add(headSignature);
            herbrand.set(headSignature, new HashSet<Literal>());
        }
        boolean changed;
        do {
            int herbrandSize0 = VectorUtils.sum(herbrand.sizes());
            Glogger.debug("herbrandSize0: " + herbrandSize0);
            Matching matching = new Matching(Sugar.<Clause>list(new Clause(Sugar.flatten(herbrand.values()))));
            for (Pair<String, Integer> predicate : headSignatures) {
                //may overwrite the previous ones which is actually what we want
                matching.getEngine().addCustomPredicate(new TupleNotIn(predicate.r, predicate.s, herbrand.get(predicate)));
            }
            for (Clause rule : rules) {
                Literal head = head(rule);
                Pair<String, Integer> headSignature = new Pair<String, Integer>(head.predicate(), head.arity());
                SolutionConsumer solutionConsumer = new HerbrandSolutionConsumer(head, headSignature, herbrand);
                matching.getEngine().addSolutionConsumer(solutionConsumer);
                if (LogicUtils.isGround(head)) {
                    Clause query = new Clause(flipSigns(rule.literals()));
                    if (matching.subsumption(query, 0)) {
                        herbrand.put(headSignature, head);
                    }
                } else {
                    Clause query = new Clause(flipSigns(Sugar.union(rule.literals(), new Literal(tupleNotInPredicateName(head.predicate(), head.arity()), true, head.arguments()))));
                    Pair<Term[], List<Term[]>> substitutions;
                    do {
                        //not super optimal but the rule grounding will dominate the runtime anyway...
                        substitutions = matching.allSubstitutions(query, 0, 512);
                    } while (substitutions.s.size() > 0);
                }
                matching.getEngine().removeSolutionConsumer(solutionConsumer);
            }
            int herbrandSize1 = VectorUtils.sum(herbrand.sizes());
            Glogger.debug("herbrandSize1 " + herbrandSize1);
            changed = herbrandSize1 > herbrandSize0;
        } while (changed);
        return Sugar.setFromCollections(Sugar.flatten(herbrand.values()));
    }

    private Literal head(Clause c) {
        for (Literal l : c.literals()) {
            if (!l.isNegated()) {
                return l;
            }
        }
        return null;
    }

    private static List<Literal> flipSigns(Iterable<Literal> c) {
        List<Literal> lits = new ArrayList<Literal>();
        for (Literal l : c) {
            lits.add(l.negation());
        }
        return lits;
    }

    private Pair<List<Clause>, List<Literal>> rulesAndFacts(List<? extends Clause> clauses) {
        List<Literal> groundFacts = new ArrayList<Literal>();
        List<Clause> rest = new ArrayList<Clause>();
        for (Clause c : clauses) {
            if (c.countLiterals() == 1 && LogicUtils.isGround(c)) {
                groundFacts.add(Sugar.chooseOne(c.literals()));
            } else {
                rest.add(c);
            }
        }
        return new Pair<List<Clause>, List<Literal>>(rest, groundFacts);
    }

    private static String tupleNotInPredicateName(String predicate, int arity) {
        return "@tuplenotin-" + predicate + "/" + arity;
    }

    private static class HerbrandSolutionConsumer implements SolutionConsumer {

        private Literal head;

        private Pair<String, Integer> headSignature;

        private MultiMap<Pair<String, Integer>, Literal> herbrand;

        private HerbrandSolutionConsumer(Literal head, Pair<String, Integer> headSignature, MultiMap<Pair<String, Integer>, Literal> herbrand) {
            this.head = head;
            this.headSignature = headSignature;
            this.herbrand = herbrand;
        }

        @Override
        public void solution(Term[] template, Term[] solution) {
            herbrand.put(headSignature, LogicUtils.substitute(head, template, solution));
        }
    }

    private static class TupleNotIn implements CustomPredicate {

        private Set<Literal> literals;

        private String name;

        private String predicate;

        TupleNotIn(String predicate, int arity, Set<Literal> literals) {
            this.predicate = predicate;
            this.name = tupleNotInPredicateName(predicate, arity);
            this.literals = literals;
        }

        @Override
        public String name() {
            return name;
        }

        @Override
        public boolean isSatisfiable(Term... arguments) {
            if (Sugar.countNulls(arguments) > 0) {
                return true;
            }
            //System.out.println("? "+!literals.contains(new Literal(predicate, arguments))+" -- "+new Literal(predicate, arguments)+" -- "+literals);
            return !literals.contains(new Literal(predicate, arguments));
        }
    }

    public static void main(String[] args) {
        List<Clause> rules = Sugar.list(
                Clause.parse("holdsK(S,P,O), !holdsL1(S,P,O)"),
                Clause.parse("similarK1s(A,B), !similar(A,B)"),
                Clause.parse("similarK1p(A,B), !similar(A,B)"),
                Clause.parse("similarK1o(A,B), !similar(A,B)"),
                Clause.parse("holdsL1(S,P,O), !similarK1s(S,concept_mammal_micinka),!similarK1p(P,generalizations),!similarK1o(O,concept_mammal_cats)"),
                Clause.parse("holdsK(S,P,O), !holdsL2(S,P,O)"),
                Clause.parse("similarK2s(A,B), !similar(A,B)"),
                Clause.parse("similarK2p(A,B),!similar(A,B)"),
                Clause.parse("similarK2o(A,B), !similar(A,B)"),
                Clause.parse("holdsL2(S,P,O),!similarK2s(S,concept_mammal_cats),!similarK2p(P,concept_mammalinducesemotion),!similarK2o(O,concept_emotion_fear)"),
                Clause.parse("holdsK(S,P,O),!holdsL3(S,P,O)"),
                Clause.parse("similarK3s(A,B),!similar(A,B)"),
                Clause.parse("similarK3p(A,B),!similar(A,B)"),
                Clause.parse("similarK3o(A,B),!similar(A,B)"),
                Clause.parse("holdsL3(S,P,O),!similarK3s(S,concept_mammal_tiger),!similarK3p(P,concept_mammalsuchasmammal),!similarK3o(O,concept_mammal_bear)"),
                Clause.parse("holdsK(A,B,C),!holdsLrek(A,B,C)"),
                Clause.parse("holdsLrek(A,B,C),!holdsK(A,generalizations,X), !holdsK(X,B,C)"),
                Clause.parse("finalL(dummy), !holdsK(S,P,O)"),
                Clause.parse("similar(X,X)")
        );

        Clause ground = Clause.parse("exists(concept_mammal_micinka,generalizations,concept_mammal_tiger,concept_mammalinducesemotion,concept_mammal_cats,concept_emotion_fear,concept_mammal_bear,concept_mammalsuchasmammal,concept_animalistypeofanimal)");

        for (Literal l : ground.literals()) {
            rules.add(new Clause(l));
        }

        int repeats = 1;
        Set<Literal> herbrand = null;
        long t1 = System.nanoTime();
        for (int i = 0; i < repeats; i++) {
            BottomUpGrounder bug = new BottomUpGrounder();
            herbrand = bug.herbrandModel(rules);
        }
        long t2 = System.nanoTime();
        for (Literal c : herbrand) {
            System.out.println(c);
        }
        System.out.println(herbrand);
        System.out.println("Time: " + (t2 - t1) / (1e6 * repeats) + "ms");

        Matching m = new Matching();
        Clause rule = Clause.parse("holdsLrek(A,B,C), holdsK(A,generalizations,X), holdsK(X,B,C)");
        Pair<Term[], List<Term[]>> pair = m.allSubstitutions(rule, new Clause(herbrand));
        for (Term[] substitution : pair.s) {
            System.out.println(LogicUtils.substitute(rule, pair.r, substitution));
        }
    }
}
