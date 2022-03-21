#include "llvm/Pass.h"
#include "llvm/IR/Function.h"
#include "llvm/IR/Instruction.h"
#include "llvm/IR/IRBuilder.h"
#include "llvm/IR/Constant.h"
#include "llvm/Support/raw_ostream.h"
#include "llvm/IR/LegacyPassManager.h"
#include "llvm/Transforms/IPO/PassManagerBuilder.h"
using namespace llvm;

namespace {
  struct SkeletonPass : public FunctionPass {
    static char ID;
    SkeletonPass() : FunctionPass(ID) {}

    virtual bool runOnFunction(Function &F) {
      errs() << "Function " << F.getName()<< "\n";
      bool changed = false;

      for (auto& B : F) {
        for (auto& I : B) {
          if(auto* op = dyn_cast<BinaryOperator>(&I)) {
            if(Instruction::isCommutative(I.getOpcode())){
              IRBuilder<> builder(op);
              Value* first = op->getOperand(0);
              Value* second = op->getOperand(1);

              if (auto* l = dyn_cast<ConstantInt>(first)) {
                if (auto* r = dyn_cast<ConstantInt>(second)){
                  if (l->getSExtValue() > r->getSExtValue()){
                    op->setOperand(0, second);
                    op->setOperand(1, first);
                    changed = true;
                  }
                }
              }
            }
          }
        }
      }
      return changed;
    }
  };
}

char SkeletonPass::ID = 0;

// Automatically enable the pass.
// http://adriansampson.net/blog/clangpass.html
static void registerSkeletonPass(const PassManagerBuilder &,
                         legacy::PassManagerBase &PM) {
  PM.add(new SkeletonPass());
}
static RegisterStandardPasses
  RegisterMyPass(PassManagerBuilder::EP_EarlyAsPossible,
                 registerSkeletonPass);
