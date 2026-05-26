(define (domain Depot)
(:requirements :strips :typing)
(:types place locatable - object
	depot distributor - place
        truck hoist surface - locatable
        pallet crate - surface)

(:predicates (available ?x - hoist) 
             (clear ?x - surface)
             (on ?x - crate ?y - surface)
             (in ?x - crate ?y - truck)
             (lifting ?x - hoist ?y - crate)
             (at ?x - locatable ?y - place))

(:action Drive
:parameters (?x - truck ?y - place ?z - place) 
:precondition (and (at ?x ?y))
:effect (and (not (at ?x ?y)) (at ?x ?z)))

(:action Load
:parameters (?x - hoist ?y - crate ?z - truck ?p - place)
:precondition (and (lifting ?x ?y) (at ?x ?p) (at ?z ?p))
:effect (and (not (lifting ?x ?y)) (in ?y ?z) (available ?x)))

(:action Unload 
:parameters (?x - hoist ?y - crate ?z - truck ?p - place)
:precondition (and (in ?y ?z) (at ?x ?p) (available ?x) (at ?z ?p))
:effect (and (lifting ?x ?y) (not (in ?y ?z)) (not (available ?x))))

(:action Lift
:parameters (?x - hoist ?y - crate ?z - surface ?p - place)
:precondition (and (clear ?y) (on ?y ?z) (at ?y ?p) (at ?x ?p) (available ?x))
:effect (and (lifting ?x ?y) (not (clear ?y)) (not (on ?y ?z)) (clear ?z) (not (at ?y ?p)) (not (available ?x))))

(:action Drop 
:parameters (?x - hoist ?y - crate ?z - surface ?p - place)
:precondition (and (lifting ?x ?y) (at ?z ?p) (clear ?z) (at ?x ?p))
:effect (and (not (lifting ?x ?y)) (at ?y ?p) (clear ?y) (on ?y ?z) (not (clear ?z)) (available ?x)))
)