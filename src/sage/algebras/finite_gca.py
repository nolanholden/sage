r"""
Finite dimensional graded commutative algebras

AUTHORS:

- Michael Jung (2021): initial version

"""

#*****************************************************************************
#       Copyright (C) 2021 Michael Jung <m.jung at vu.nl>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
#                  http://www.gnu.org/licenses/
#*****************************************************************************

from sage.combinat.free_module import CombinatorialFreeModule
from sage.categories.algebras import Algebras
from sage.misc.cachefunc import cached_method
from sage.combinat.integer_vector_weighted import WeightedIntegerVectors
from sage.rings.ring import Algebra
from sage.misc.functional import is_odd, is_even
from sage.sets.disjoint_union_enumerated_sets import DisjointUnionEnumeratedSets
from sage.sets.condition_set import ConditionSet
from sage.rings.integer_ring import ZZ

class FiniteGCAlgebra(CombinatorialFreeModule, Algebra):
    r"""
    Finite dimensional graded commutative algebras.

    A finite dimensional graded commutative algebra `A` is an integer-graded
    algebra satisfying the super-algebra relation w.r.t. the degree modulo 2.
    More precisely, `A` has a graded ring structure

    .. MATH::

        A = \bigoplus_{i=0}^n A_i,

    where `n \in \NN` is the finite maximal degree, and the multiplication
    satisfies

    .. MATH::

        A_i \cdot A_j \subset \begin{cases}A_{i+j} & \text{if $i+j\leq n$}, \\
                                             0 & \text{if $i+j > n$},\end{cases}

    as well as the super-algebra relation

    .. MATH::

        x y = (-1)^{ij} y x

    for all homogeneous elements `x \in A_i` and `y \in A_j`.

    Such an algebra is multiplicatively generated by a set of single monomials
    `\{ x_1, \ldots, x_k \}`, where each `x_i` is given a certain degree
    `\mathrm{deg}(x_i)`. To that end, this algebra can be given a vector
    space basis, and the basis vectors are of the form `x_1^{w_1} \cdots x_n^{
    w_k}`, where `\sum_{i=1}^k \mathrm{deg}(x_i) \, w_i \leq n` and

    .. MATH::

        w_i \in \begin{cases} \ZZ_2 & \text{if $\mathrm{deg}(x_i)$ is odd}, \\
        \NN & \text{if $\mathrm{deg}(x_i)$ is even}. \end{cases}

    Typical examples of finite dimensional graded commutative algebras are
    cohomology rings over finite dimensional CW-complexes.

    INPUT:

    - ``base`` -- the base field
    - ``names`` -- (optional) names of the generators: a list of
      strings or a single string with the names separated by
      commas. If not specified, the generators are named "x0", "x1",...
    - ``degrees`` -- (optional) a tuple or list specifying the degrees
      of the generators; if omitted, each generator is given degree
      1, and if both ``names`` and ``degrees`` are omitted, an error is
      raised.
    - ``max_degree`` -- the maximal degree of the graded algebra.
    - ``mul_symbol`` -- (optional) symbol used for multiplication. If omitted,
      the string "*" is used.
    - ``mul_latex_symbol`` -- (optional) latex symbol used for multiplication.
      If omitted, the empty string is used.

    EXAMPLES::

        sage: A.<x,y,z,t> = GradedCommutativeAlgebra(QQ, degrees=(1,2,2,3), max_degree=6)
        sage: A
        Graded commutative algebra with generators ('x', 'y', 'z', 't') in degrees (1, 2, 2, 3) with maximal degree 6
        sage: t*x + x*t
        0
        sage: x^2
        0
        sage: x*t^2
        0
        sage: x*y^2+z*t
        x*y^2 + z*t

    The generators can be returned with :meth:`algebra_generators`::

        sage: F = A.algebra_generators(); F
        Family (x, y, z, t)
        sage: [g.degree() for g in F]
        [1, 2, 2, 3]

    We can also return the basis::

        sage: list(A.basis())
        [1, x, z, y, t, x*z, x*y, x*t, z^2, y*z, y^2, z*t, y*t, x*z^2, x*y*z, x*y^2]

    Depending on the context, the multiplication can be given a different
    symbol::

        sage: A.<x,y,z,t> = GradedCommutativeAlgebra(QQ, degrees=(1,2,6,6), max_degree=10, mul_symbol='⌣', mul_latex_symbol=r'\smile')
        sage: x*y^2 + x*t
        x⌣y^2 + x⌣t
        sage: latex(x*y^2 - z*x)
        x\smile y^{2} - x\smile z

    .. NOTE::

        Notice, when the argument ``max_degree`` in the global namespace is
        omitted, an instance of the class
        :class:`sage.algebras.commutative_dga.GCAlgebra` is created instead::

            sage: A.<x,y,z,t> = GradedCommutativeAlgebra(QQ, degrees=(1,2,6,6))
            sage: type(A)
            <class 'sage.algebras.commutative_dga.GCAlgebra_with_category'>

    """
    @staticmethod
    def __classcall_private__(cls, base, names=None, degrees=None,
                              max_degree=None, category=None, **kwargs):
        r"""
        Normalize the input for the :meth:`__init__` method and the
        unique representation.

        INPUT:

        - ``base`` -- the base ring of the algebra
        - ``max_degree`` -- the maximal degree of the algebra
        - ``names`` -- the names of the variables; by default, set to ``x1``,
          ``x2``, etc.
        - ``degrees`` -- the degrees of the generators; by default, set to 1

        TESTS::

            sage: A1 = GradedCommutativeAlgebra(GF(2), 'x,y', (3, 6), max_degree=12)
            sage: A2 = GradedCommutativeAlgebra(GF(2), ['x', 'y'], [3, 6], max_degree=12)
            sage: A1 is A2
            True

        """
        if max_degree is None:
            raise TypeError("max_degree must be specified")
        if names is None:
            if degrees is None:
                raise ValueError("You must specify names or degrees")
            else:
                n = len(degrees)
            names = tuple('x{}'.format(i) for i in range(n))
        elif isinstance(names, str):
            names = tuple(names.split(','))
            n = len(names)
        else:
            n = len(names)
            names = tuple(names)
        if degrees is None:
            degrees = tuple([1 for _ in range(n)])
        else:
            degrees = tuple(degrees)

        return super().__classcall__(cls, base=base, names=names,
                                     degrees=degrees, max_degree=max_degree,
                                     category=category, **kwargs)

    def __init__(self, base, names, degrees, max_degree,
                 category=None, **kwargs):
        r"""
        Construct a commutative graded algebra with finite degree.

        TESTS::

            sage: A.<x,y,z,t> = GradedCommutativeAlgebra(QQ, max_degree=6)
            sage: TestSuite(A).run()
            sage: A = GradedCommutativeAlgebra(QQ, ('x','y','z'), [2,3,4], max_degree=8)
            sage: TestSuite(A).run()
            sage: A = GradedCommutativeAlgebra(QQ, ('x','y','z','t'), [1,2,3,4], max_degree=10)
            sage: TestSuite(A).run()

        """
        from sage.arith.misc import gcd

        if max_degree not in ZZ:
            raise TypeError('max_degree must be an integer')
        if max_degree < max(degrees):
            raise ValueError(f'max_degree must not deceed {max(degrees)}')
        self._names = names
        self.__ngens = len(self._names)
        self._degrees = degrees
        self._max_deg = max_degree
        self._weighted_vectors = WeightedIntegerVectors(degrees)
        self._mul_symbol = kwargs.pop('mul_symbol', '*')
        self._mul_latex_symbol = kwargs.pop('mul_latex_symbol', '')
        step = gcd(degrees)
        universe = DisjointUnionEnumeratedSets(self._weighted_vectors.subset(k)
                                               for k in range(0, max_degree, step))
        base_cat = Algebras(base).WithBasis().Super().Supercommutative().FiniteDimensional()
        category = base_cat.or_subcategory(category, join=True)
        indices = ConditionSet(universe, self._valid_index)
        sorting_key = self._weighted_vectors.grading
        CombinatorialFreeModule.__init__(self, base, indices,
                                         sorting_key=sorting_key,
                                         category=category)

    def _valid_index(self, w):
        r"""
        Return whether ``w`` is a valid index; no multiple powers in odd
        degrees.

        TESTS::

            sage: A.<x,y,z> = GradedCommutativeAlgebra(QQ, degrees=(1,2,3), max_degree=8)
            sage: w1 = A._weighted_vectors([1,2,1])
            sage: w2 = A._weighted_vectors([1,2,2])
            sage: A._valid_index(w1)
            True
            sage: A._valid_index(w2)
            False

        """
        return not any(i > 1 for i, d in zip(w, self._degrees) if is_odd(d))

    def _repr_(self):
        """
        Return the string representation of ``self``.

        TESTS::

            sage: A.<x,y,z> = GradedCommutativeAlgebra(QQ, degrees=(1,2,3), max_degree=8)
            sage: A._repr_()
            "Graded commutative algebra with generators ('x', 'y', 'z') in degrees (1, 2, 3) with maximal degree 8"
            sage: A  # indirect doctest
            Graded commutative algebra with generators ('x', 'y', 'z') in degrees (1, 2, 3) with maximal degree 8

        """
        desc = f'Graded commutative algebra with generators {self._names} in '
        desc += f'degrees {self._degrees} with maximal degree {self._max_deg}'
        return desc

    def ngens(self):
        r"""
        Return the number of generators of ``self``.

        EXAMPLES::

            sage: A.<x,y,z> = GradedCommutativeAlgebra(QQ, degrees=(4,8,2), max_degree=10)
            sage: A.ngens()
            3

        """
        return self.__ngens

    @cached_method
    def product_on_basis(self, w1, w2):
        r"""
        Return the product of two indices within the algebra.

        EXAMPLES::

            sage: A.<x,y,z> = GradedCommutativeAlgebra(QQ, degrees=(4,8,2), max_degree=10)
            sage: z*x
            x*z
            sage: x^3
            0
            sage: 5*z + 4*z*x
            5*z + 4*x*z

        ::

            sage: A.<x,y,z> = GradedCommutativeAlgebra(QQ, degrees=(1,2,3), max_degree=5)
            sage: 2*x*y
            2*x*y
            sage: x^2
            0
            sage: x*z
            x*z
            sage: z*x
            -x*z
            sage: x*y*z
            0

        TESTS::

            sage: A.<x,y,z> = GradedCommutativeAlgebra(QQ, degrees=(4,8,2), max_degree=10)
            sage: weighted_vectors = A._weighted_vectors
            sage: w1 = A._weighted_vectors([1,0,1])
            sage: w2 = A._weighted_vectors([0,0,0])
            sage: A.product_on_basis(w1, w2)
            x*z

        ::

            sage: A.<x,y,z> = GradedCommutativeAlgebra(QQ, degrees=(1,2,3), max_degree=5)
            sage: weighted_vectors = A._weighted_vectors
            sage: w1 = A._weighted_vectors([1,0,0])
            sage: w2 = A._weighted_vectors([0,0,1])
            sage: A.product_on_basis(w1, w2)
            x*z
            sage: A.product_on_basis(w2, w1)
            -x*z

        ::

            sage: A.<x,y,z> = GradedCommutativeAlgebra(QQ, degrees=(1,2,3), max_degree=10)
            sage: weighted_vectors = A._weighted_vectors
            sage: w1 = A._weighted_vectors([1,1,0])
            sage: w2 = A._weighted_vectors([0,1,1])
            sage: A.product_on_basis(w1, w2)
            x*y^2*z
            sage: A.product_on_basis(w2, w1)
            -x*y^2*z

        """
        grading = self._weighted_vectors.grading
        deg_left = grading(w1)
        deg_right = grading(w2)
        deg_tot = deg_left + deg_right
        if deg_tot > self._max_deg:
            return self.zero()
        w_tot = self._weighted_vectors([sum(w) for w in zip(w1, w2)])
        if not self._valid_index(w_tot):
            return self.zero()
        # determine sign
        n = self.__ngens
        c = 0
        for p, i, d in zip(reversed(range(n)), reversed(w1), reversed(self._degrees)):
            if is_even(d) or i == 0:
                continue
            for q, j, b in zip(range(n), w2, self._degrees):
                if q == p:
                    break
                if j == 0 or is_even(b):
                    continue
                c += 1
        return (-1)**c * self.monomial(w_tot)

    def degree_on_basis(self, i):
        r"""
        Return the degree of a homogeneous element with index `i`.

        EXAMPLES::

            sage: A.<a,b,c> = GradedCommutativeAlgebra(QQ, degrees=(2,4,6), max_degree=7)
            sage: a.degree()
            2
            sage: (2*a*b).degree()
            6
            sage: (a+b).degree()
            Traceback (most recent call last):
            ...
            ValueError: element is not homogeneous

        TESTS::

            sage: A.<a,b,c> = GradedCommutativeAlgebra(QQ, degrees=(2,4,6), max_degree=7)
            sage: weighted_vectors = A._weighted_vectors
            sage: i = A._weighted_vectors([1,1,0])
            sage: A.degree_on_basis(i)
            6

        """
        return self._weighted_vectors.grading(i)

    def _repr_term(self, w):
        r"""
        Return the string representation of basis with index ``w``.

        TESTS::

            sage: A.<x,y,z> = GradedCommutativeAlgebra(QQ, degrees=(1,2,3), max_degree=8)
            sage: w = A._weighted_vectors([1,2,1])
            sage: A._repr_term(w)
            'x*y^2*z'
            sage: x*y^2*z  # indirect doctest
            x*y^2*z

        ::

            sage: A.<x,y,z> = GradedCommutativeAlgebra(QQ, degrees=(1,2,3), max_degree=8, mul_symbol='⌣')
            sage: w = A._weighted_vectors([1,2,1])
            sage: A._repr_term(w)
            'x⌣y^2⌣z'
            sage: x*y^2*z  # indirect doctest
            x⌣y^2⌣z

        """
        # Trivial case:
        if sum(w) == 0:
            return '1'
        # Non-trivial case:
        terms = []
        for i in range(len(w)):
            if w[i] == 0:
                continue
            elif w[i] == 1:
                terms.append(self._names[i])
            else:
                terms.append(self._names[i] + f'^{w[i]}')
        return self._mul_symbol.join(terms)

    def _latex_term(self, w):
        r"""
        Return the LaTeX representation of basis with index ``w``.

        TESTS::

            sage: A.<x,y,z> = GradedCommutativeAlgebra(QQ, degrees=(1,2,3), max_degree=8)
            sage: w = A._weighted_vectors([1,2,1])
            sage: A._latex_term(w)
            'x y^{2} z'
            sage: latex(x*y^2*z)  # indirect doctest
            x y^{2} z

        ::

            sage: A.<x,y,z> = GradedCommutativeAlgebra(QQ, degrees=(1,2,3), max_degree=8, mul_latex_symbol=r'\smile')
            sage: A._latex_term(w)
            'x\\smile y^{2}\\smile z'
            sage: latex(x*y^2*z)  # indirect doctest
            x\smile y^{2}\smile z

        """
        # Trivial case:
        if sum(w) == 0:
            return '1'
        # Non-trivial case:
        terms = []
        for i in range(len(w)):
            if w[i] == 0:
                continue
            elif w[i] == 1:
                terms.append(self._names[i])
            else:
                terms.append(self._names[i] + '^{' + str(w[i]) + '}')
        latex_mul = self._mul_latex_symbol + ' '  # add whitespace
        return latex_mul.join(terms)

    def algebra_generators(self):
        r"""
        Return the generators of ``self`` as a
        :class:`sage.sets.family.TrivialFamily`.

        EXAMPLES::

            sage: A.<x,y,z> = GradedCommutativeAlgebra(QQ, degrees=(4,8,2), max_degree=10)
            sage: A.algebra_generators()
            Family (x, y, z)

        """
        from sage.sets.family import Family

        return Family(self.gens())

    @cached_method
    def one_basis(self):
        r"""
        Return the index of the one element of ``self``.

        EXAMPLES::

            sage: A.<x,y,z> = GradedCommutativeAlgebra(QQ, degrees=(4,8,2), max_degree=10)
            sage: ind = A.one_basis(); ind
            [0, 0, 0]
            sage: A.monomial(ind)
            1
            sage: A.one()  # indirect doctest
            1

        """
        n = len(self._degrees)
        return self._weighted_vectors([0 for _ in range(n)])

    def gens(self):
        r"""
        Return the generators of ``self`` as a list.

        EXAMPLES::

            sage: A.<x,y,z> = GradedCommutativeAlgebra(QQ, degrees=(4,8,2), max_degree=10)
            sage: A.gens()
            [x, y, z]

        """
        n = len(self._degrees)
        zero = [0 for _ in range(n)]
        indices = []
        for k in range(n):
            ind = list(zero)
            ind[k] = 1
            indices.append(self._weighted_vectors(ind))
        return [self.monomial(ind) for ind in indices]

    @cached_method
    def gen(self, i):
        r"""
        Return the `i`-th generator of ``self``.

        EXAMPLES::

            sage: A.<x,y,z> = GradedCommutativeAlgebra(QQ, degrees=(4,8,2), max_degree=10)
            sage: A.gen(0)
            x
            sage: A.gen(1)
            y
            sage: A.gen(2)
            z

        """
        return self.gens()[i]

    def maximal_degree(self):
        r"""
        Return the maximal degree of ``self``.

        EXAMPLES::

            sage: A.<x,y,z> = GradedCommutativeAlgebra(QQ, degrees=(1,2,3), max_degree=8)
            sage: A.maximal_degree()
            8

        """
        return self._max_deg

    max_degree = maximal_degree