# -*- coding: utf-8 -*-

__author__ = 'iankuoli'

import networkx as nx
import scipy.sparse as sp
import numpy as np
import operator
import RelationshipEvaluator as re

class GraphProcessor:

    @staticmethod
    def row_normalize(cc):
        v = cc.sum(axis=1).T
        for k in range(v.size):
            if v[0, k] == 0:
                v[0, k] = 1e-20

        ccd = sp.spdiags(1. / v, 0, *cc.shape)
        return ccd * cc

    @staticmethod
    def sym_normalize(cc):
        v = np.power(cc.sum(axis=1).T, 0.5)
        for k in range(v.size):
            if v[0, k] == 0:
                v[0, k] = 1e-20
        ccd = sp.spdiags(1. / v, 0, *cc.shape)
        return ccd * cc * ccd

    def __init__(self):
        self.G = nx.Graph()
        self.dupboss_A = sp.csr_matrix()
        self.comivst_A = sp.csr_matrix()
        self.sym_dupboss_A = sp.csr_matrix()
        self.sym_comivst_A = sp.csr_matrix()
        self.dupboss_edgesNum = 0
        self.comivst_edgesNum = 0
        self.edgesNum = 0
        self.nodesNum = 0
        self.nodelist = list()

    def load_graph(self, file_path):
        f_graph = open(file_path, 'r')
        for line in f_graph:
            l = line.strip('\n').split('\t')
            com1 = l[0]
            com2 = l[1]
            w = float(l[2])
            self.G.add_edge(com1, com2, dupbossjaccard=w)

    def add_edge(self, u, v, boss_u, boss_v):
        # u: the id (統編) of company u
        # v: the id (統編) of company u
        # boss_u: the boss set of company u, e.g., "王建隆", "王北海"
        # boss_v: the boss set of company u, e.g., "王建隆", "王北海", "王建超"
        share_boss = boss_u & boss_v
        all_boss = boss_u | boss_v
        w = len(share_boss) / len(all_boss)
        self.G.add_edge(u, v, dupbossjaccard=w)

    def to_sparse(self):
        self.nodelist = list(self.G.nodes())
        self.nodesNum = len(self.nodelist)
        self.edgesNum = len(self.G.edges())
        self.dupboss_A = nx.to_scipy_sparse_matrix(self.G, nodelist=self.nodelist, weight='dupbossjaccard', dtype=float)
        self.comivst_A = nx.to_scipy_sparse_matrix(self.G, nodelist=self.nodelist, weight='comivstratio', dtype=float)

    def sym_norm(self):
        self.sym_dupboss_A = self.sym_normalize(self.dupboss_A)
        self.sym_comivst_A = self.sym_normalize(self.comivst_A)

    def relationship_eval(self, rel_def, func_def, query):

        if len(self.dupboss_A) == 0 or len(self.comivst_A) == 0:
            self.to_sparse()
        if len(self.sym_dupboss_A) == 0 or len(self.sym_comivst_A) == 0:
            self.sym_norm()

        if rel_def == 1:
            tmpA = self.sym_dupboss_A
        else:
            tmpA = self.sym_comivst_A

        # query: "com1,com2,com3,... \t winner"
        q_list = query.strip('\n').split('\t')
        tenders = list(q_list[0].split(','))

        # {(com1, com2):distance, ...}
        ret_dict = dict()

        if len(q_list) == 2:
            # with winner
            winner = q_list[1]
            if winner not in self.nodelist or len(tenders) == 1 or winner == '-1':
                return 'winner or tender data is wrong'

            if func_def == 1:
                # (TKDE, 2007)
                # Random-Walk Computation of Similarities between Nodes of a Graph with Application to
                # Collaborative Recommendation
                for d in tenders:

                    if d not in self.nodelist or winner == d:
                        continue

                    distance = re.rw_sim(winner, d, tmpA, self.nodelist)
                    ret_dict[(winner, d)] = distance

            elif func_def == 2:
                #
                # ???
                #
                for d in tenders:

                    if d not in self.nodelist or winner == d:
                        continue

                    distance = re.rw_sim(winner, d, tmpA, self.nodelist)
                    ret_dict[(winner, d)] = distance

            else:
                return 'index of rel_def is wrong'
        else:
            # without winner
            if func_def == 1:
                # (TKDE, 2007)
                # Random-Walk Computation of Similarities between Nodes of a Graph with Application to
                # Collaborative Recommendation
                for i in range(len(tenders)):
                    com1 = tenders[i]
                    if com1 not in self.nodelist:
                        continue

                    for j in range(i+1, len(tenders)):
                        com2 = tenders[j]

                        if com2 not in self.nodelist:
                            continue

                        distance = re.rw_sim(com1, com2, tmpA, self.nodelist)
                        ret_dict[(com1, com2)] = distance

            elif func_def == 2:
                #
                # ???
                #
                for i in range(len(tenders)):
                    com1 = tenders[i]
                    if com1 not in self.nodelist:
                        continue

                    for j in range(i+1, len(tenders)):
                        com2 = tenders[j]

                        if com2 not in self.nodelist:
                            continue

                        distance = re.rw_sim(com1, com2, tmpA, self.nodelist)
                        ret_dict[(com1, com2)] = distance

            else:
                return 'index of rel_def is wrong'

        return ret_dict
