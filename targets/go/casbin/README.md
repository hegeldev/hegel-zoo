# go/casbin

[casbin/casbin](https://github.com/casbin/casbin) — an authorization library: a model language
(request, policy and role definitions, a policy effect and a matcher expression), a policy of
rules, role hierarchies with domains, a management and an RBAC API, adapters to persist the
policy. Pinned at `524f3f2` (master, 2026-09-11, eleven commits after v3.11.0). Apache-2.0.

## Oracle

The documentation of the model language and of the APIs (casbin.org, "Syntax for models",
"Management API", "RBAC API", "RBAC with domains"), evaluated in a small model:

- a universe of four users, three roles, a superuser, three objects (or paths and patterns for
  keyMatch and keyMatch2, or objects and resource roles for g2), two actions, two domains;
- generated model specifications: with or without domains (`g = _, _, _`), a role hierarchy
  (`g(r.sub, p.sub[, r.dom])`) or plain subjects, resource roles (`g2`), an `eft` field, one of
  the four effects (`some(where (p.eft == allow))`, `!some(where (p.eft == deny))`, both,
  `priority(p.eft) || deny`), an explicit `priority` field, object matching by equality,
  `keyMatch` or `keyMatch2`, a superuser clause;
- generated policies (p rules, g links, g2 links) without duplicates.

The model evaluates a request as the documentation describes: the role closure over the g rules
(per domain), the matcher per rule, then the effect over the matched rules (first allow; no
deny; allow and no deny; first determinate rule in priority order).

## Properties

- `TestHegelEnforceAgreesWithModel`: on every request of the universe Enforce, EnforceEx and
  BatchEnforce decide as the model, and EnforceEx reports the deciding rule.
- `TestHegelRBACQueriesAgreeWithModel`: GetRolesForUser, GetUsersForRole, HasRoleForUser,
  GetImplicitRolesForUser, GetImplicitUsersForRole, GetPermissionsForUser,
  GetImplicitPermissionsForUser, GetImplicitObjectPatternsForUser, GetImplicitUsersForPermission,
  GetAllSubjects/Objects/Actions/Roles/Users, GetAllDomains, GetDomainsForUser,
  GetAllUsersByDomain, GetAllRolesByDomain, GetImplicitUsersForResource(ByDomain),
  GetFilteredPolicy and GetFilteredNamedPolicyWithMatcher against the model's closures and rule
  lists.
- `TestHegelMutationsAgreeWithModel`: a sequence of Add/Remove/Update(Filtered) policies and
  grouping policies, AddRoleForUser, DeleteRoleForUser, DeleteRolesForUser, DeleteUser,
  DeleteRole, DeletePermission(sForUser), DeleteAllUsersByDomain, DeleteDomains, ClearPolicy
  returns what the documentation says, leaves the rules the model has (no duplicates), and
  afterwards Enforce, the implicit roles and the domains agree with the model (incremental role
  links).
- `TestHegelKeyMatchPatterns`, `TestHegelKeyMatchPrefix`: keyMatch..keyMatch5, keyGet,
  keyGet2, keyGet3 against the documented pattern languages (`*`, `/*`, `:name`, `{name}`,
  repeated names, query strings) with a backtracking matcher written from the documentation.
- `TestHegelPolicySaveLoadRoundTrip`: a policy with awkward field values (spaces, commas,
  quotes, `#`, tabs, non-ASCII, empty) saved by the file adapter and by the string adapter loads
  back as the same rules.
- `TestHegelModelTextRoundTrip`: `Model.ToText` loads back to a model with the same text and the
  same decisions.

## Bugs

Sixteen, in bugs.toml: ClearPolicy keeps the role links (1); an update to an existing rule
duplicates it (2); UpdateFilteredPolicies without an updatable adapter adds and never removes
(3); GetAllDomains keeps emptied domains (4); DeleteUser fails without a role definition (5);
trailing whitespace of the last field lost on save/load (6); a role cycle the API accepts fails
to load (7); the string adapter cannot load an empty policy (8); ToText is not deterministic
(9); GetDomainsForUser lists "" with a domain-less g2 (10); GetImplicitUsersForResourceByDomain
ignores the domain of user rules (11); GetImplicitUsersForResource expands roles one level only
(12); keyMatch3/4/5 read `{a}_{b}` as one placeholder (13); rules keyed by comma-joined fields
collide (14); GetImplicitPermissionsForUser (15) and GetAllUsersByDomain (16) read the subject
from field 0 and break on the documented explicit-priority policy.

Quirks kept out of the bug list: a `g2` definition is only loaded when `g` is defined too (the
section is read as g, g2, g3, ... until the first missing key), so the generated models always
define `g`; a `*` in a keyMatch2..5 pattern not preceded by `/`, and regexp metacharacters such
as `.`, are passed to the regexp as they are (the code comments acknowledge it), so the
generated patterns avoid them; the role manager's pattern matching functions
(AddNamedMatchingFunc) are not covered.

## History

- 2026-09-21 (turn 348): target created at 524f3f2; 16 bugs, 16 pins.
