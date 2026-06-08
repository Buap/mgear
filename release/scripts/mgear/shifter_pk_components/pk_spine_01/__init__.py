import mgear.pymaya as pm
from mgear.pymaya import datatypes

from mgear.shifter import component

from mgear.core import node, fcurve, applyop, vector, curve
from mgear.core import attribute, transform, primitive

import maya.cmds as cmds

#############################################
# COMPONENT
#############################################


class Component(component.Main):
    """Shifter component Class"""

    # =====================================================
    # OBJECTS
    # =====================================================
    def addObjects(self):

        #ИК контролы
        t1 = transform.getTransformLookingAt(self.guide.apos[0], self.guide.apos[1], self.guide.blades["blade"].z * -1, "yx", self.negate)
        fk_npo = primitive.addTransform(self.root, self.getName("ikBtm_npo"), t1)
        fk_btm_ctl = self.addCtl(fk_npo, "ikBtm_ctl", t1, self.color_fk, "cube",  w=self.size * .2,  h=self.size * .1,  d=self.size * .1)
        self.btm_cnx = fk_btm_ctl

        t2 = transform.setMatrixPosition(t1, self.guide.apos[1])
        fk1_npo = primitive.addTransform(self.root, self.getName("ikTop_npo"), t2)
        fk_top_ctl = self.addCtl(fk1_npo, "ikTop_ctl", t2, self.color_fk, "cube",  w=self.size * .2,  h=self.size * .1,  d=self.size * .1)
        self.top_cnx = fk_top_ctl

        t3 = transform.getInterpolateTransformMatrix(t1, t2, 0.5)
        fk2_npo = primitive.addTransform(self.root, self.getName("ikMid_npo"), t3)
        fk_mid_ctl = self.addCtl(fk2_npo, "ikMid_ctl", t3, self.color_fk, "cube",  w=self.size * .2,  h=self.size * .1,  d=self.size * .1)

        dist = transform.getDistance2(fk_btm_ctl,fk_top_ctl)

        #Локальные контролы
        joints = []
        joints_npo = []
        for i in range(5):
            loc_dist = 1/4 * i
            t = transform.getInterpolateTransformMatrix(fk_btm_ctl, fk_top_ctl, loc_dist)

            prnt = None
            if(i<2):
                prnt = fk_btm_ctl
            if(i==2):
                prnt = fk_mid_ctl
            if(i>2):
                prnt = fk_top_ctl

            loc_npo = primitive.addTransform(prnt, self.getName("local%s" % (i)), t)
            loc_ctl = self.addCtl(loc_npo, "local%s_ctl" % i, t, self.color_fk, "sphere",  w=self.size * .1,  h=self.size * .1,  d=self.size * .1)

            joints_npo.append(loc_npo)

            j = primitive.addJoint(loc_ctl, self.getName(("jnt%s") % i), t)
            joints.append(self.getName(("jnt%s") % i))

        cmds.pointConstraint(joints_npo[1], joints_npo[3], fk2_npo)
        cmds.aimConstraint(joints_npo[3], fk2_npo, offset=(0,0,0), weight=1, aimVector=(0,1,0), upVector=(1,0,0), worldUpType="objectrotation", worldUpVector=(1,0,0), worldUpObject=self.root)

        #риббон
        nurbs_surface_name = self.getName("ribbonSrfc")
        nurbs_surface = cmds.nurbsPlane(name=self.getName("ribbonSrfc"), width=1, lengthRatio=dist, patchesU=1, patchesV=2)
    
        nurbs_surface_npo = primitive.addTransform(self.setupWS, self.getName("ribbonSrfc_npo"), t1)
        cmds.parent(nurbs_surface, nurbs_surface_npo)

        cmds.xform(nurbs_surface, translation=[0,dist/2,0], rotation=[0,-90,0], scale=[1,1,self.size * .05])
        cmds.makeIdentity(nurbs_surface, apply=True)
        cmds.rebuildSurface(nurbs_surface, ch=1, rpo=1, rt=0, end=0, kr=0, kcp=0, kc=0, su=1, du=1, sv=2, dv=3, tol=0.01, fr=0, dir=2)

        cmds.delete(nurbs_surface, constructionHistory=True)


        skin_elements = joints + [nurbs_surface_name]
        cmds.skinCluster(skin_elements, toSelectedBones=True, bindMethod=0, skinMethod=0, name="skinCluster1")

        #ФК контролы
        fk_controls = []
        for k,v in enumerate(joints):
            if(k>0 and k<4):
                prnt = None
                if(k==1):
                    prnt = self.root
                elif(k>=2):
                   prnt = fk_controls[k - 2]

                t = transform.getTransform(joints_npo[k])
                fk_npo = primitive.addTransform(prnt, self.getName("fk%s_npo" % (k - 1)), t)
                fk_ctl = self.addCtl(fk_npo, "fk%s_ctl" % (k - 1), t, (self.color_fk), "circle",  w=self.size,  h=self.size,  d=self.size, degree=3)
                fk_controls.append(fk_ctl)

        cmds.parent(fk1_npo, fk_controls[-1])

        self.jnt_pos.append(
            {
                "obj":fk_btm_ctl,
                "name":0,
                "UniScale":False
            }
        )

        self.jnt_pos.append(
            {
                "obj":fk_top_ctl,
                "name":1,
                "UniScale":False
            }
        )

        # """Add all the objects needed to create the component."""

        # t = transform.getTransformLookingAt(
        #     self.guide.apos[0],
        #     self.guide.apos[1],
        #     self.guide.blades["blade"].z * -1,
        #     "yx",
        #     self.negate)

        # t2 = transform.setMatrixPosition(t, self.guide.apos[1])

        # int_t = t
        # self.preiviousCtlTag = self.parentCtlTag

        # # FK Controlers ------------------------------------
        # self.fk_btm_ctl = []
        # self.fk_npo = []
        # parentctl = self.root
        # blend_increment = 1.0 / (self.settings["division"] - 1)
        # blend_val = 0.0
        # for i in range(self.settings["division"]):
        #     fk_npo = primitive.addTransform(
        #         parentctl,
        #         self.getName("fk%s_npo" % (i)),
        #         int_t)

        #     self.fk_npo.append(fk_npo)

        #     fk_btm_ctl = self.addCtl(fk_npo,
        #                          "fk%s_ctl" % (i),
        #                          int_t,
        #                          self.color_fk,
        #                          "cube",
        #                          w=self.size,
        #                          h=self.size * .05,
        #                          d=self.size,
        #                          tp=self.preiviousCtlTag)

        #     self.fk_btm_ctl.append(fk_btm_ctl)
        #     self.preiviousCtlTag = fk_btm_ctl

        #     parentctl = fk_btm_ctl

        #     blend_val = blend_val + blend_increment

        #     int_t = transform.getInterpolateTransformMatrix(
        #         t, t2, blend=blend_val)

        # for x in self.fk_btm_ctl:
        #     attribute.setKeyableAttributes(x)
        #     attribute.setRotOrder(x, "ZXY")
        #     attribute.setInvertMirror(x, ["tx", "rz", "ry"])

        # # Ik Controlers ------------------------------------

        # self.ik0_npo = primitive.addTransform(
        #     self.fk_btm_ctl[0], self.getName("ik0_npo"), t)
        # self.ik0_ctl = self.addCtl(self.ik0_npo,
        #                            "ik0_ctl",
        #                            t,
        #                            self.color_ik,
        #                            "compas",
        #                            w=self.size,
        #                            tp=self.parentCtlTag)

        # attribute.setKeyableAttributes(self.ik0_ctl, self.tr_params)
        # attribute.setRotOrder(self.ik0_ctl, "ZXY")
        # attribute.setInvertMirror(self.ik0_ctl, ["tx", "ry", "rz"])

        # t = transform.setMatrixPosition(t, self.guide.apos[1])
        # self.ik1_npo = primitive.addTransform(
        #     self.fk_btm_ctl[-1], self.getName("ik1_npo"), t)

        # self.ik1_ctl = self.addCtl(self.ik1_npo,
        #                            "ik1_ctl",
        #                            t,
        #                            self.color_ik,
        #                            "compas",
        #                            w=self.size,
        #                            tp=self.ik0_ctl)

        # attribute.setKeyableAttributes(self.ik1_ctl, self.tr_params)
        # attribute.setRotOrder(self.ik1_ctl, "ZXY")
        # attribute.setInvertMirror(self.ik1_ctl, ["tx", "ry", "rz"])

        # # Tangent controllers -------------------------------
        # if self.settings["centralTangent"]:
        #     vec_pos = vector.linearlyInterpolate(self.guide.apos[0],
        #                                          self.guide.apos[1],
        #                                          .33)
        #     t = transform.setMatrixPosition(t, vec_pos)

        #     self.tan0_npo = primitive.addTransform(
        #         self.ik0_ctl, self.getName("tan0_npo"), t)

        #     self.tan0_off = primitive.addTransform(
        #         self.tan0_npo, self.getName("tan0_off"), t)

        #     self.tan0_ctl = self.addCtl(self.tan0_off,
        #                                 "tan0_ctl",
        #                                 t,
        #                                 self.color_ik,
        #                                 "sphere",
        #                                 w=self.size * .1,
        #                                 tp=self.ik0_ctl)

        #     attribute.setKeyableAttributes(self.tan0_ctl, self.t_params)
        #     vec_pos = vector.linearlyInterpolate(self.guide.apos[0],
        #                                          self.guide.apos[1],
        #                                          .66)

        #     t = transform.setMatrixPosition(t, vec_pos)

        #     self.tan1_npo = primitive.addTransform(
        #         self.ik1_ctl, self.getName("tan1_npo"), t)

        #     self.tan1_off = primitive.addTransform(
        #         self.tan1_npo, self.getName("tan1_off"), t)

        #     self.tan1_ctl = self.addCtl(self.tan1_off,
        #                                 "tan1_ctl",
        #                                 t,
        #                                 self.color_ik,
        #                                 "sphere",
        #                                 w=self.size * .1,
        #                                 tp=self.ik0_ctl)

        #     attribute.setKeyableAttributes(self.tan1_ctl, self.t_params)

        #     # Tangent mid control
        #     vec_pos = vector.linearlyInterpolate(self.guide.apos[0],
        #                                          self.guide.apos[1],
        #                                          .5)
        #     t = transform.setMatrixPosition(t, vec_pos)

        #     self.tan_npo = primitive.addTransform(
        #         self.tan0_npo, self.getName("tan_npo"), t)

        #     self.tan_ctl = self.addCtl(self.tan_npo,
        #                                "tan_ctl",
        #                                t,
        #                                self.color_fk,
        #                                "sphere",
        #                                w=self.size * .2,
        #                                tp=self.ik1_ctl)

        #     attribute.setKeyableAttributes(self.tan_ctl, self.t_params)
        #     attribute.setInvertMirror(self.tan_ctl, ["tx"])

        # else:
        #     vec_pos = vector.linearlyInterpolate(self.guide.apos[0],
        #                                          self.guide.apos[1],
        #                                          .33)

        #     t = transform.setMatrixPosition(t, vec_pos)

        #     self.tan0_npo = primitive.addTransform(
        #         self.ik0_ctl, self.getName("tan0_npo"), t)

        #     self.tan0_ctl = self.addCtl(self.tan0_npo,
        #                                 "tan0_ctl",
        #                                 t,
        #                                 self.color_ik,
        #                                 "sphere",
        #                                 w=self.size * .2,
        #                                 tp=self.ik0_ctl)

        #     attribute.setKeyableAttributes(self.tan0_ctl, self.t_params)

        #     vec_pos = vector.linearlyInterpolate(self.guide.apos[0],
        #                                          self.guide.apos[1],
        #                                          .66)

        #     t = transform.setMatrixPosition(t, vec_pos)

        #     self.tan1_npo = primitive.addTransform(
        #         self.ik1_ctl, self.getName("tan1_npo"), t)

        #     self.tan1_ctl = self.addCtl(self.tan1_npo,
        #                                 "tan1_ctl",
        #                                 t,
        #                                 self.color_ik,
        #                                 "sphere",
        #                                 w=self.size * .2,
        #                                 tp=self.ik1_ctl)

        #     attribute.setKeyableAttributes(self.tan1_ctl, self.t_params)

        # attribute.setInvertMirror(self.tan0_ctl, ["tx"])
        # attribute.setInvertMirror(self.tan1_ctl, ["tx"])

        # # Curves -------------------------------------------
        # self.mst_crv = curve.addCnsCurve(
        #     self.root,
        #     self.getName("mst_crv"),
        #     [self.ik0_ctl, self.tan0_ctl, self.tan1_ctl, self.ik1_ctl],
        #     3)
        # self.slv_crv = curve.addCurve(self.root, self.getName("slv_crv"),
        #                               [datatypes.Vector()] * 10,
        #                               False,
        #                               3)
        # self.mst_crv.setAttr("visibility", False)
        # self.slv_crv.setAttr("visibility", False)

        # # Division -----------------------------------------
        # # The user only define how many intermediate division he wants.
        # # First and last divisions are an obligation.
        # parentdiv = self.root
        # parentctl = self.root
        # self.div_cns = []
        # self.scl_transforms = []
        # self.twister = []
        # self.ref_twist = []

        # t = transform.getTransformLookingAt(
        #     self.guide.apos[0],
        #     self.guide.apos[1],
        #     self.guide.blades["blade"].z * -1,
        #     "yx",
        #     self.negate)

        # parent_twistRef = primitive.addTransform(
        #     self.root,
        #     self.getName("reference"),
        #     transform.getTransform(self.root))

        # self.jointList = []
        # self.preiviousCtlTag = self.parentCtlTag
        # for i in range(self.settings["division"]):

        #     # References
        #     div_cns = primitive.addTransform(parentdiv,
        #                                      self.getName("%s_cns" % i))
        #     pm.setAttr(div_cns + ".inheritsTransform", False)
        #     self.div_cns.append(div_cns)
        #     parentdiv = div_cns

        #     parentctl = div_cns
        #     scl_ref = primitive.addTransform(parentctl,
        #                                      self.getName("%s_scl_ref" % i),
        #                                      transform.getTransform(parentctl))

        #     self.scl_transforms.append(scl_ref)

        #     # Deformers (Shadow)
        #     self.jnt_pos.append([scl_ref, i])

        #     # Twist references (This objects will replace the spinlookup
        #     # slerp solver behavior)
        #     t = transform.getTransformLookingAt(
        #         self.guide.apos[0],
        #         self.guide.apos[1],
        #         self.guide.blades["blade"].z * -1,
        #         "yx",
        #         self.negate)

        #     twister = primitive.addTransform(
        #         parent_twistRef, self.getName("%s_rot_ref" % i), t)

        #     ref_twist = primitive.addTransform(
        #         parent_twistRef, self.getName("%s_pos_ref" % i), t)

        #     ref_twist.setTranslation(
        #         datatypes.Vector(1.0, 0, 0), space="preTransform")

        #     self.twister.append(twister)
        #     self.ref_twist.append(ref_twist)

        # # Connections (Hooks) ------------------------------
        # self.cnx0 = primitive.addTransform(self.root, self.getName("0_cnx"))
        # self.cnx1 = primitive.addTransform(self.root, self.getName("1_cnx"))

    def addAttributes(self):

        # Anim -------------------------------------------
        self.position_att = self.addAnimParam(
            "position", "Position", "double", self.settings["position"], 0, 1)

        self.maxstretch_att = self.addAnimParam("maxstretch",
                                                "Max Stretch",
                                                "double",
                                                self.settings["maxstretch"],
                                                1)

        self.maxsquash_att = self.addAnimParam("maxsquash",
                                               "Max Squash",
                                               "double",
                                               self.settings["maxsquash"],
                                               0,
                                               1)

        self.softness_att = self.addAnimParam(
            "softness", "Softness", "double", self.settings["softness"], 0, 1)

        self.tan0_att = self.addAnimParam("tan0", "Tangent 0", "double", 1, 0)
        self.tan1_att = self.addAnimParam("tan1", "Tangent 1", "double", 1, 0)

        # Volume
        self.volume_att = self.addAnimParam(
            "volume", "Volume", "double", 1, 0, 1)

        # Setup ------------------------------------------
        # Eval Fcurve
        if self.guide.paramDefs["st_profile"].value:
            self.st_value = self.guide.paramDefs["st_profile"].value
            self.sq_value = self.guide.paramDefs["sq_profile"].value
        else:
            self.st_value = fcurve.getFCurveValues(self.settings["st_profile"],
                                                   self.divisions)
            self.sq_value = fcurve.getFCurveValues(self.settings["sq_profile"],
                                                   self.divisions)

        self.st_att = [self.addSetupParam("stretch_%s" % i,
                                          "Stretch %s" % i,
                                          "double",
                                          self.st_value[i],
                                          -1,
                                          0)
                       for i in range(self.settings["division"])]

        self.sq_att = [self.addSetupParam("squash_%s" % i,
                                          "Squash %s" % i,
                                          "double",
                                          self.sq_value[i],
                                          0,
                                          1)
                       for i in range(self.settings["division"])]

    # =====================================================
    # OPERATORS
    # =====================================================
    def addOperators(self):
        pass
        # """Create operators and set the relations for the component rig

        # Apply operators, constraints, expressions to the hierarchy.
        # In order to keep the code clean and easier to debug,
        # we shouldn't create any new object in this method.

        # """

        # # Tangent position ---------------------------------
        # # common part
        # d = vector.getDistance(self.guide.apos[0], self.guide.apos[1])
        # dist_node = node.createDistNode(self.ik0_ctl, self.ik1_ctl)
        # rootWorld_node = node.createDecomposeMatrixNode(
        #     self.root.attr("worldMatrix"))

        # div_node = node.createDivNode(dist_node + ".distance",
        #                               rootWorld_node + ".outputScaleX")

        # div_node = node.createDivNode(div_node + ".outputX", d)

        # # tan0
        # mul_node = node.createMulNode(self.tan0_att,
        #                               self.tan0_npo.getAttr("ty"))

        # res_node = node.createMulNode(mul_node + ".outputX",
        #                               div_node + ".outputX")

        # pm.connectAttr(res_node + ".outputX", self.tan0_npo.attr("ty"))

        # # tan1
        # mul_node = node.createMulNode(self.tan1_att,
        #                               self.tan1_npo.getAttr("ty"))

        # res_node = node.createMulNode(mul_node + ".outputX",
        #                               div_node + ".outputX")

        # pm.connectAttr(res_node + ".outputX", self.tan1_npo.attr("ty"))

        # # Tangent Mid --------------------------------------
        # if self.settings["centralTangent"]:
        #     tanIntMat = applyop.gear_intmatrix_op(
        #         self.tan0_npo.attr("worldMatrix"),
        #         self.tan1_npo.attr("worldMatrix"),
        #         .5)

        #     applyop.gear_mulmatrix_op(
        #         tanIntMat.attr("output"),
        #         self.tan_npo.attr("parentInverseMatrix[0]"),
        #         self.tan_npo)

        #     pm.connectAttr(self.tan_ctl.attr("translate"),
        #                    self.tan0_off.attr("translate"))

        #     pm.connectAttr(self.tan_ctl.attr("translate"),
        #                    self.tan1_off.attr("translate"))

        # # Curves -------------------------------------------
        # op = applyop.gear_curveslide2_op(
        #     self.slv_crv, self.mst_crv, 0, 1.5, .5, .5)

        # pm.connectAttr(self.position_att, op + ".position")
        # pm.connectAttr(self.maxstretch_att, op + ".maxstretch")
        # pm.connectAttr(self.maxsquash_att, op + ".maxsquash")
        # pm.connectAttr(self.softness_att, op + ".softness")

        # # Volume driver ------------------------------------
        # crv_node = node.createCurveInfoNode(self.slv_crv)

        # # Division -----------------------------------------
        # for i in range(self.settings["division"]):

        #     # References
        #     u = i / (self.settings["division"] - 1.0)

        #     cns = applyop.pathCns(
        #         self.div_cns[i], self.slv_crv, False, u, True)

        #     cns.setAttr("frontAxis", 1)  # front axis is 'Y'
        #     cns.setAttr("upAxis", 0)  # front axis is 'X'

        #     # Roll
        #     intMatrix = applyop.gear_intmatrix_op(
        #         self.ik0_ctl + ".worldMatrix",
        #         self.ik1_ctl + ".worldMatrix",
        #         u)

        #     dm_node = node.createDecomposeMatrixNode(intMatrix + ".output")
        #     pm.connectAttr(dm_node + ".outputRotate",
        #                    self.twister[i].attr("rotate"))

        #     pm.parentConstraint(self.twister[i],
        #                         self.ref_twist[i],
        #                         maintainOffset=True)

        #     pm.connectAttr(self.ref_twist[i] + ".translate",
        #                    cns + ".worldUpVector")

        #     # Squash n Stretch
        #     op = applyop.gear_squashstretch2_op(self.scl_transforms[i],
        #                                         self.root,
        #                                         pm.arclen(self.slv_crv),
        #                                         "y")

        #     pm.connectAttr(self.volume_att, op + ".blend")
        #     pm.connectAttr(crv_node + ".arcLength", op + ".driver")
        #     pm.connectAttr(self.st_att[i], op + ".stretch")
        #     pm.connectAttr(self.sq_att[i], op + ".squash")

        # # Connections (Hooks) ------------------------------
        # pm.pointConstraint(self.scl_transforms[0], self.cnx0)
        # pm.scaleConstraint(self.scl_transforms[0], self.cnx0)
        # pm.orientConstraint(self.ik0_ctl, self.cnx0)
        # pm.pointConstraint(self.scl_transforms[-1], self.cnx1)
        # pm.scaleConstraint(self.scl_transforms[-1], self.cnx1)
        # pm.orientConstraint(self.ik1_ctl, self.cnx1)

    # =====================================================
    # CONNECTOR
    # =====================================================
    def setRelation(self):
        self.relatives["eff"] = self.top_cnx
        self.relatives["root"] = self.btm_cnx

        self.jointRelatives["root"] = 0
        self.jointRelatives["eff"] = -1

        # """Set the relation beetween object from guide to rig"""
        # self.relatives["root"] = self.cnx0
        # self.relatives["eff"] = self.cnx1

        # self.controlRelatives["root"] = self.fk_btm_ctl[0]
        # self.controlRelatives["eff"] = self.fk_btm_ctl[-1]

        # self.jointRelatives["root"] = 0
        # self.jointRelatives["eff"] = -1

        # self.aliasRelatives["root"] = "base"
        # self.aliasRelatives["eff"] = "tip"
